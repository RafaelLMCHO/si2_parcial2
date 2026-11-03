CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_audit_row()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_empresa uuid;
    v_entidad_id uuid;
    v_usuario uuid;
    v_antes jsonb;
    v_despues jsonb;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_empresa := OLD.empresa_id;
        v_entidad_id := OLD.id;
        v_antes := to_jsonb(OLD) - 'password_hash' - 'refresh_token_hash';
    ELSIF TG_OP = 'UPDATE' THEN
        v_empresa := NEW.empresa_id;
        v_entidad_id := NEW.id;
        v_antes := to_jsonb(OLD) - 'password_hash' - 'refresh_token_hash';
        v_despues := to_jsonb(NEW) - 'password_hash' - 'refresh_token_hash';
    ELSE
        v_empresa := NEW.empresa_id;
        v_entidad_id := NEW.id;
        v_despues := to_jsonb(NEW) - 'password_hash' - 'refresh_token_hash';
    END IF;

    BEGIN
        v_usuario := NULLIF(current_setting('app.usuario_id', true), '')::uuid;
    EXCEPTION WHEN others THEN
        v_usuario := NULL;
    END;

    INSERT INTO bitacora_auditoria (
        empresa_id,
        usuario_id,
        actor_tipo,
        accion,
        entidad,
        entidad_id,
        datos_antes,
        datos_despues
    ) VALUES (
        v_empresa,
        v_usuario,
        'usuario',
        CASE TG_OP
            WHEN 'INSERT' THEN 'insert'
            WHEN 'UPDATE' THEN 'update'
            ELSE 'delete'
        END,
        TG_TABLE_NAME,
        v_entidad_id,
        v_antes,
        v_despues
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_usuario_rol()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_rol_empresa uuid;
    v_rol_global boolean;
    v_sucursal_empresa uuid;
BEGIN
    SELECT empresa_id, es_global
      INTO v_rol_empresa, v_rol_global
      FROM rol
     WHERE id = NEW.rol_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El rol no existe';
    END IF;

    IF v_rol_global AND NEW.empresa_id IS NOT NULL THEN
        RAISE EXCEPTION 'Un rol global no puede asignarse a un usuario de tenant';
    END IF;

    IF NEW.empresa_id IS NULL AND NOT v_rol_global THEN
        RAISE EXCEPTION 'Un usuario sin tenant requiere un rol global';
    END IF;

    IF NEW.empresa_id IS NOT NULL AND v_rol_empresa IS DISTINCT FROM NEW.empresa_id THEN
        RAISE EXCEPTION 'El rol no pertenece al tenant del usuario';
    END IF;

    IF NEW.sucursal_id IS NOT NULL THEN
        SELECT empresa_id
          INTO v_sucursal_empresa
          FROM sucursal
         WHERE id = NEW.sucursal_id;

        IF v_sucursal_empresa IS DISTINCT FROM NEW.empresa_id THEN
            RAISE EXCEPTION 'La sucursal no pertenece al tenant del usuario';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_limite_sucursales()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_limite integer;
    v_actuales integer;
BEGIN
    IF NEW.estado <> 'activa' OR NEW.deleted_at IS NOT NULL THEN
        RETURN NEW;
    END IF;

    SELECT pl.limite
      INTO v_limite
      FROM suscripcion s
      JOIN plan_limite pl
        ON pl.plan_id = s.plan_id
       AND pl.recurso = 'sucursales'
     WHERE s.empresa_id = NEW.empresa_id
       AND s.estado IN ('prueba', 'activa', 'mora')
     ORDER BY s.fecha_inicio DESC, s.created_at DESC
     LIMIT 1;

    IF v_limite IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT count(*)
      INTO v_actuales
      FROM sucursal
     WHERE empresa_id = NEW.empresa_id
       AND estado = 'activa'
       AND deleted_at IS NULL
       AND id <> NEW.id;

    IF v_actuales + 1 > v_limite THEN
        RAISE EXCEPTION 'Límite de sucursales del plan alcanzado (%)', v_limite;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_actualizar_stock_reservado()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sucursal_id uuid;
    v_estado varchar(20);
    v_liberada_en timestamptz;
    v_old_sucursal_id uuid;
    v_old_estado varchar(20);
    v_old_liberada_en timestamptz;
    v_filas integer;
BEGIN
    IF TG_OP = 'DELETE' THEN
        SELECT sucursal_id, estado, liberada_en
          INTO v_sucursal_id, v_estado, v_liberada_en
          FROM reserva
         WHERE id = OLD.reserva_id
           AND empresa_id = OLD.empresa_id;

        IF NOT FOUND THEN
            RETURN OLD;
        END IF;

        IF v_liberada_en IS NOT NULL
           OR v_estado IN ('cancelada', 'expirada', 'convertida', 'completada') THEN
            RETURN OLD;
        END IF;

        UPDATE inventario
           SET stock_reservado = stock_reservado - OLD.cantidad,
               actualizado_en = now()
         WHERE empresa_id = OLD.empresa_id
           AND variante_id = OLD.variante_id
           AND sucursal_id = v_sucursal_id
           AND stock_reservado >= OLD.cantidad;

        GET DIAGNOSTICS v_filas = ROW_COUNT;
        IF v_filas = 0 THEN
            RAISE EXCEPTION 'No se pudo liberar el stock reservado';
        END IF;

        RETURN OLD;
    END IF;

    SELECT sucursal_id, estado, liberada_en
      INTO v_sucursal_id, v_estado, v_liberada_en
      FROM reserva
     WHERE id = NEW.reserva_id
       AND empresa_id = NEW.empresa_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La reserva no existe';
    END IF;

    IF v_liberada_en IS NOT NULL
       OR v_estado IN ('cancelada', 'expirada', 'convertida', 'completada') THEN
        RAISE EXCEPTION 'No se puede modificar el detalle de una reserva cerrada';
    END IF;

    IF TG_OP = 'INSERT' THEN
        UPDATE inventario
           SET stock_reservado = stock_reservado + NEW.cantidad,
               actualizado_en = now()
         WHERE empresa_id = NEW.empresa_id
           AND variante_id = NEW.variante_id
           AND sucursal_id = v_sucursal_id;

        GET DIAGNOSTICS v_filas = ROW_COUNT;
        IF v_filas = 0 THEN
            RAISE EXCEPTION 'No existe inventario para la variante y sucursal';
        END IF;

        RETURN NEW;
    END IF;

    IF OLD.reserva_id = NEW.reserva_id
       AND OLD.variante_id = NEW.variante_id
       AND OLD.cantidad = NEW.cantidad THEN
        RETURN NEW;
    END IF;

    SELECT sucursal_id, estado, liberada_en
      INTO v_old_sucursal_id, v_old_estado, v_old_liberada_en
      FROM reserva
     WHERE id = OLD.reserva_id
       AND empresa_id = OLD.empresa_id;

    IF FOUND
       AND v_old_liberada_en IS NULL
       AND v_old_estado NOT IN ('cancelada', 'expirada', 'convertida', 'completada') THEN
        UPDATE inventario
           SET stock_reservado = stock_reservado - OLD.cantidad,
               actualizado_en = now()
         WHERE empresa_id = OLD.empresa_id
           AND variante_id = OLD.variante_id
           AND sucursal_id = v_old_sucursal_id
           AND stock_reservado >= OLD.cantidad;

        GET DIAGNOSTICS v_filas = ROW_COUNT;
        IF v_filas = 0 THEN
            RAISE EXCEPTION 'No se pudo liberar el stock reservado anterior';
        END IF;
    END IF;

    UPDATE inventario
       SET stock_reservado = stock_reservado + NEW.cantidad,
           actualizado_en = now()
     WHERE empresa_id = NEW.empresa_id
       AND variante_id = NEW.variante_id
       AND sucursal_id = v_sucursal_id;

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas = 0 THEN
        RAISE EXCEPTION 'No existe inventario para la variante y sucursal';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_recalcular_total_venta()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_venta_id uuid;
    v_empresa_id uuid;
    v_subtotal numeric(12,2);
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_venta_id := OLD.venta_id;
        v_empresa_id := OLD.empresa_id;
    ELSE
        v_venta_id := NEW.venta_id;
        v_empresa_id := NEW.empresa_id;
    END IF;

    SELECT COALESCE(SUM(subtotal), 0)
      INTO v_subtotal
      FROM venta_detalle
     WHERE venta_id = v_venta_id
       AND empresa_id = v_empresa_id;

    UPDATE venta
       SET subtotal = v_subtotal,
           total = v_subtotal - descuento + impuesto,
           updated_at = now()
     WHERE id = v_venta_id
       AND empresa_id = v_empresa_id;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_pago_venta()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_total numeric(12,2);
    v_pagado numeric(12,2);
BEGIN
    IF NEW.estado <> 'completado' THEN
        RETURN NEW;
    END IF;

    SELECT total
      INTO v_total
      FROM venta
     WHERE id = NEW.venta_id
       AND empresa_id = NEW.empresa_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La venta no existe';
    END IF;

    SELECT COALESCE(SUM(monto), 0)
      INTO v_pagado
      FROM pago
     WHERE empresa_id = NEW.empresa_id
       AND venta_id = NEW.venta_id
       AND estado = 'completado'
       AND id <> NEW.id;

    IF v_pagado + NEW.monto > v_total THEN
        RAISE EXCEPTION 'El pago excede el total de la venta';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_cambio()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_cantidad integer;
    v_ya_devuelta integer;
BEGIN
    SELECT cantidad
      INTO v_cantidad
      FROM venta_detalle
     WHERE id = NEW.venta_detalle_id
       AND empresa_id = NEW.empresa_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El detalle de venta no existe';
    END IF;

    SELECT COALESCE(SUM(cantidad), 0)
      INTO v_ya_devuelta
      FROM cambio_detalle
     WHERE empresa_id = NEW.empresa_id
       AND venta_detalle_id = NEW.venta_detalle_id
       AND id <> NEW.id;

    IF v_ya_devuelta + NEW.cantidad > v_cantidad THEN
        RAISE EXCEPTION 'La cantidad devuelta o cambiada excede la cantidad vendida';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_cupon()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_cupon cupon%ROWTYPE;
    v_usos integer;
    v_usos_usuario integer;
BEGIN
    PERFORM pg_advisory_xact_lock(
        hashtextextended(NEW.empresa_id::text || ':' || NEW.cupon_id::text, 0)
    );

    SELECT *
      INTO v_cupon
      FROM cupon
     WHERE id = NEW.cupon_id
       AND empresa_id = NEW.empresa_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El cupón no existe';
    END IF;

    IF NOT v_cupon.activo
       OR now() < v_cupon.fecha_inicio
       OR now() >= v_cupon.fecha_fin THEN
        RAISE EXCEPTION 'El cupón no está vigente';
    END IF;

    SELECT count(*)
      INTO v_usos
      FROM cupon_uso
     WHERE empresa_id = NEW.empresa_id
       AND cupon_id = NEW.cupon_id;

    IF v_cupon.usos_maximos IS NOT NULL AND v_usos >= v_cupon.usos_maximos THEN
        RAISE EXCEPTION 'El cupón está agotado';
    END IF;

    SELECT count(*)
      INTO v_usos_usuario
      FROM cupon_uso
     WHERE empresa_id = NEW.empresa_id
       AND cupon_id = NEW.cupon_id
       AND usuario_id = NEW.usuario_id;

    IF v_cupon.usos_por_usuario IS NOT NULL
       AND v_usos_usuario >= v_cupon.usos_por_usuario THEN
        RAISE EXCEPTION 'El usuario alcanzó el límite de usos del cupón';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_registrar_historial_venta()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario uuid;
BEGIN
    IF NEW.estado IS DISTINCT FROM OLD.estado THEN
        BEGIN
            v_usuario := NULLIF(current_setting('app.usuario_id', true), '')::uuid;
        EXCEPTION WHEN others THEN
            v_usuario := NULL;
        END;

        INSERT INTO venta_estado_historial (
            empresa_id,
            venta_id,
            estado_anterior,
            estado_nuevo,
            usuario_id
        ) VALUES (
            NEW.empresa_id,
            NEW.id,
            OLD.estado,
            NEW.estado,
            v_usuario
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_liberar_stock_reserva()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sucursal_id uuid;
    v_filas integer;
    r record;
BEGIN
    IF OLD.estado = NEW.estado THEN
        RETURN NEW;
    END IF;

    IF OLD.estado NOT IN ('activa', 'confirmada')
       OR NEW.estado NOT IN ('cancelada', 'expirada', 'convertida', 'completada')
       OR NEW.liberada_en IS NOT NULL THEN
        RETURN NEW;
    END IF;

    SELECT sucursal_id
      INTO v_sucursal_id
      FROM reserva
     WHERE id = NEW.id
       AND empresa_id = NEW.empresa_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La reserva no existe';
    END IF;

    FOR r IN
        SELECT variante_id, cantidad
          FROM reserva_detalle
         WHERE empresa_id = NEW.empresa_id
           AND reserva_id = NEW.id
    LOOP
        UPDATE inventario
           SET stock_reservado = stock_reservado - r.cantidad,
               actualizado_en = now()
         WHERE empresa_id = NEW.empresa_id
           AND variante_id = r.variante_id
           AND sucursal_id = v_sucursal_id
           AND stock_reservado >= r.cantidad;

        GET DIAGNOSTICS v_filas = ROW_COUNT;
        IF v_filas = 0 THEN
            RAISE EXCEPTION 'No se pudo liberar el stock de la reserva';
        END IF;
    END LOOP;

    NEW.liberada_en := now();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_registrar_historial_reserva()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario uuid;
BEGIN
    IF NEW.estado IS DISTINCT FROM OLD.estado THEN
        BEGIN
            v_usuario := NULLIF(current_setting('app.usuario_id', true), '')::uuid;
        EXCEPTION WHEN others THEN
            v_usuario := NULL;
        END;

        INSERT INTO reserva_estado_historial (
            empresa_id,
            reserva_id,
            estado_anterior,
            estado_nuevo,
            motivo,
            usuario_id
        ) VALUES (
            NEW.empresa_id,
            NEW.id,
            OLD.estado,
            NEW.estado,
            NEW.motivo_cierre,
            v_usuario
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_expirar_reservas()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_count integer;
BEGIN
    UPDATE reserva
       SET estado = 'expirada',
           motivo_cierre = COALESCE(motivo_cierre, 'Expirada automáticamente'),
           updated_at = now()
     WHERE estado IN ('activa', 'confirmada')
       AND expira_en <= now();

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$;

CREATE OR REPLACE FUNCTION fn_bump_catalogo_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_empresa_id uuid;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_empresa_id := OLD.empresa_id;
    ELSE
        v_empresa_id := NEW.empresa_id;
    END IF;

    INSERT INTO catalogo_version (empresa_id, version, actualizado_en)
    VALUES (v_empresa_id, 1, now())
    ON CONFLICT (empresa_id)
    DO UPDATE SET
        version = catalogo_version.version + 1,
        actualizado_en = now();

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT c.relname
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
          JOIN pg_attribute a ON a.attrelid = c.oid
         WHERE n.nspname = 'public'
           AND c.relkind IN ('r', 'p')
           AND c.relispartition = false
           AND a.attname = 'updated_at'
           AND a.attnum > 0
           AND NOT a.attisdropped
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%I_updated_at ON %I',
            r.relname,
            r.relname
        );
        EXECUTE format(
            'CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()',
            r.relname,
            r.relname
        );
    END LOOP;
END $$;

CREATE TRIGGER trg_usuario_validar_rol
    BEFORE INSERT OR UPDATE ON usuario
    FOR EACH ROW EXECUTE FUNCTION fn_validar_usuario_rol();

CREATE TRIGGER trg_sucursal_limite_plan
    BEFORE INSERT OR UPDATE OF estado ON sucursal
    FOR EACH ROW EXECUTE FUNCTION fn_validar_limite_sucursales();

CREATE TRIGGER trg_reserva_detalle_stock
    AFTER INSERT OR UPDATE OR DELETE ON reserva_detalle
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_stock_reservado();

CREATE TRIGGER trg_venta_detalle_total
    AFTER INSERT OR UPDATE OR DELETE ON venta_detalle
    FOR EACH ROW EXECUTE FUNCTION fn_recalcular_total_venta();

CREATE TRIGGER trg_pago_total
    BEFORE INSERT OR UPDATE ON pago
    FOR EACH ROW EXECUTE FUNCTION fn_validar_pago_venta();

CREATE TRIGGER trg_cambio_detalle_cantidad
    BEFORE INSERT OR UPDATE ON cambio_detalle
    FOR EACH ROW EXECUTE FUNCTION fn_validar_cambio();

CREATE TRIGGER trg_cupon_uso_validar
    BEFORE INSERT ON cupon_uso
    FOR EACH ROW EXECUTE FUNCTION fn_validar_cupon();

CREATE TRIGGER trg_venta_historial_estado
    AFTER UPDATE OF estado ON venta
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_historial_venta();

CREATE TRIGGER trg_audit_usuario
    AFTER INSERT OR UPDATE OR DELETE ON usuario
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_sucursal
    AFTER INSERT OR UPDATE OR DELETE ON sucursal
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_suscripcion
    AFTER INSERT OR UPDATE OR DELETE ON suscripcion
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_cupon
    AFTER INSERT OR UPDATE OR DELETE ON cupon
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_prenda
    AFTER INSERT OR UPDATE OR DELETE ON prenda
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_variante
    AFTER INSERT OR UPDATE OR DELETE ON variante
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_precio_historial
    AFTER INSERT OR UPDATE OR DELETE ON precio_historial
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_inventario
    AFTER INSERT OR UPDATE OR DELETE ON inventario
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_audit_venta
    AFTER INSERT OR UPDATE OR DELETE ON venta
    FOR EACH ROW EXECUTE FUNCTION fn_audit_row();

CREATE TRIGGER trg_reserva_liberar_stock
    BEFORE UPDATE OF estado ON reserva
    FOR EACH ROW EXECUTE FUNCTION fn_liberar_stock_reserva();

CREATE TRIGGER trg_reserva_historial_estado
    AFTER UPDATE OF estado ON reserva
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_historial_reserva();

CREATE TRIGGER trg_catalogo_version_prenda
    AFTER INSERT OR UPDATE OR DELETE ON prenda
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_variante
    AFTER INSERT OR UPDATE OR DELETE ON variante
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_categoria
    AFTER INSERT OR UPDATE OR DELETE ON categoria
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_temporada
    AFTER INSERT OR UPDATE OR DELETE ON temporada
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_coleccion
    AFTER INSERT OR UPDATE OR DELETE ON coleccion
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_proveedor
    AFTER INSERT OR UPDATE OR DELETE ON proveedor
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_precio_historial
    AFTER INSERT OR UPDATE OR DELETE ON precio_historial
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();

CREATE TRIGGER trg_catalogo_version_prenda_recurso
    AFTER INSERT OR UPDATE OR DELETE ON prenda_recurso
    FOR EACH ROW EXECUTE FUNCTION fn_bump_catalogo_version();
