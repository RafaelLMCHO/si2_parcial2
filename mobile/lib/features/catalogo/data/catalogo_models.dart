double? _toDouble(dynamic value) {
  if (value == null) {
    return null;
  }
  if (value is num) {
    return value.toDouble();
  }
  return double.tryParse(value.toString().replaceAll(',', '.'));
}

int? _toInt(dynamic value) {
  if (value == null) {
    return null;
  }
  if (value is num) {
    return value.toInt();
  }
  return int.tryParse(value.toString());
}

String? _toOptionalString(dynamic value) {
  final text = value?.toString().trim();
  return text == null || text.isEmpty ? null : text;
}

DateTime? _toDate(dynamic value) {
  final text = _toOptionalString(value);
  return text == null ? null : DateTime.tryParse(text);
}

class ItemSimple {
  const ItemSimple({required this.id, required this.nombre, this.extra});

  final String id;
  final String nombre;
  final String? extra;

  factory ItemSimple.fromJson(Map<String, dynamic> json) {
    return ItemSimple(
      id: json['id']?.toString() ?? '',
      nombre: json['nombre']?.toString() ?? '',
      extra: _toOptionalString(json['extra']),
    );
  }

  Map<String, dynamic> toJson() {
    return {'id': id, 'nombre': nombre, 'extra': extra};
  }
}

class VariantePrenda {
  const VariantePrenda({
    required this.id,
    required this.prendaId,
    required this.tallaId,
    required this.colorId,
    required this.sku,
    required this.precioVenta,
    required this.costo,
    required this.estado,
    this.tallaNombre,
    this.colorNombre,
    this.colorHex,
    this.codigoBarras,
    this.createdAt,
    this.updatedAt,
  });

  final String id;
  final String prendaId;
  final int tallaId;
  final String? tallaNombre;
  final int colorId;
  final String? colorNombre;
  final String? colorHex;
  final String sku;
  final String? codigoBarras;
  final double precioVenta;
  final double costo;
  final String estado;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory VariantePrenda.fromJson(Map<String, dynamic> json) {
    return VariantePrenda(
      id: json['id']?.toString() ?? '',
      prendaId: json['prenda_id']?.toString() ?? '',
      tallaId: _toInt(json['talla_id']) ?? 0,
      tallaNombre: _toOptionalString(json['talla_nombre']),
      colorId: _toInt(json['color_id']) ?? 0,
      colorNombre: _toOptionalString(json['color_nombre']),
      colorHex: _toOptionalString(json['color_hex']),
      sku: json['sku']?.toString() ?? '',
      codigoBarras: _toOptionalString(json['codigo_barras']),
      precioVenta: _toDouble(json['precio_venta']) ?? 0,
      costo: _toDouble(json['costo']) ?? 0,
      estado: json['estado']?.toString() ?? 'activa',
      createdAt: _toDate(json['created_at']),
      updatedAt: _toDate(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'prenda_id': prendaId,
      'talla_id': tallaId,
      'talla_nombre': tallaNombre,
      'color_id': colorId,
      'color_nombre': colorNombre,
      'color_hex': colorHex,
      'sku': sku,
      'codigo_barras': codigoBarras,
      'precio_venta': precioVenta,
      'costo': costo,
      'estado': estado,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}

class Prenda {
  const Prenda({
    required this.id,
    required this.codigo,
    required this.nombre,
    required this.genero,
    required this.precioBase,
    required this.moneda,
    required this.categoriaId,
    required this.estado,
    this.empresaId,
    this.descripcion,
    this.marca,
    this.categoriaNombre,
    this.temporadaId,
    this.temporadaNombre,
    this.coleccionId,
    this.coleccionNombre,
    this.proveedorId,
    this.proveedorNombre,
    this.imagenUrl,
    this.createdAt,
    this.updatedAt,
    this.variantes = const [],
  });

  final String id;
  final String? empresaId;
  final String codigo;
  final String nombre;
  final String? descripcion;
  final String? marca;
  final String genero;
  final double precioBase;
  final String moneda;
  final String categoriaId;
  final String? categoriaNombre;
  final String? temporadaId;
  final String? temporadaNombre;
  final String? coleccionId;
  final String? coleccionNombre;
  final String? proveedorId;
  final String? proveedorNombre;
  final String? imagenUrl;
  final String estado;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final List<VariantePrenda> variantes;

  factory Prenda.fromJson(Map<String, dynamic> json) {
    final rawVariantes = json['variantes'];
    return Prenda(
      id: json['id']?.toString() ?? '',
      empresaId: _toOptionalString(json['empresa_id']),
      codigo: json['codigo']?.toString() ?? '',
      nombre: json['nombre']?.toString() ?? '',
      descripcion: _toOptionalString(json['descripcion']),
      marca: _toOptionalString(json['marca']),
      genero: json['genero']?.toString() ?? 'unisex',
      precioBase: _toDouble(json['precio_base']) ?? 0,
      moneda: json['moneda']?.toString() ?? 'BOB',
      categoriaId: json['categoria_id']?.toString() ?? '',
      categoriaNombre: _toOptionalString(json['categoria_nombre']),
      temporadaId: _toOptionalString(json['temporada_id']),
      temporadaNombre: _toOptionalString(json['temporada_nombre']),
      coleccionId: _toOptionalString(json['coleccion_id']),
      coleccionNombre: _toOptionalString(json['coleccion_nombre']),
      proveedorId: _toOptionalString(json['proveedor_id']),
      proveedorNombre: _toOptionalString(json['proveedor_nombre']),
      imagenUrl: _toOptionalString(json['imagen_url']),
      estado: json['estado']?.toString() ?? 'activa',
      createdAt: _toDate(json['created_at']),
      updatedAt: _toDate(json['updated_at']),
      variantes: rawVariantes is List
          ? rawVariantes
                .whereType<Map>()
                .map(
                  (item) =>
                      VariantePrenda.fromJson(Map<String, dynamic>.from(item)),
                )
                .toList(growable: false)
          : const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'empresa_id': empresaId,
      'codigo': codigo,
      'nombre': nombre,
      'descripcion': descripcion,
      'marca': marca,
      'genero': genero,
      'precio_base': precioBase,
      'moneda': moneda,
      'categoria_id': categoriaId,
      'categoria_nombre': categoriaNombre,
      'temporada_id': temporadaId,
      'temporada_nombre': temporadaNombre,
      'coleccion_id': coleccionId,
      'coleccion_nombre': coleccionNombre,
      'proveedor_id': proveedorId,
      'proveedor_nombre': proveedorNombre,
      'imagen_url': imagenUrl,
      'estado': estado,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'variantes': variantes.map((v) => v.toJson()).toList(growable: false),
    };
  }

  List<String> get tallasDisponibles {
    final values = <String>{};
    for (final variante in variantes) {
      final label = variante.tallaNombre;
      if (label != null && label.isNotEmpty) {
        values.add(label);
      }
    }
    return values.toList(growable: false);
  }

  List<ItemSimple> get coloresDisponibles {
    final values = <String, ItemSimple>{};
    for (final variante in variantes) {
      final label = variante.colorNombre;
      if (label == null || label.isEmpty) {
        continue;
      }
      values.putIfAbsent(
        variante.colorId.toString(),
        () => ItemSimple(
          id: variante.colorId.toString(),
          nombre: label,
          extra: variante.colorHex,
        ),
      );
    }
    return values.values.toList(growable: false);
  }
}

class PrendaListResponse {
  const PrendaListResponse({
    required this.total,
    required this.versionCatalogo,
    required this.items,
  });

  final int total;
  final int versionCatalogo;
  final List<Prenda> items;

  factory PrendaListResponse.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    return PrendaListResponse(
      total: _toInt(json['total']) ?? 0,
      versionCatalogo: _toInt(json['version_catalogo']) ?? 0,
      items: rawItems is List
          ? rawItems
                .whereType<Map>()
                .map((item) => Prenda.fromJson(Map<String, dynamic>.from(item)))
                .toList(growable: false)
          : const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total': total,
      'version_catalogo': versionCatalogo,
      'items': items.map((item) => item.toJson()).toList(growable: false),
    };
  }
}

class AuxiliaresCatalogo {
  const AuxiliaresCatalogo({
    this.categorias = const [],
    this.colores = const [],
    this.tallas = const [],
    this.temporadas = const [],
    this.colecciones = const [],
  });

  final List<ItemSimple> categorias;
  final List<ItemSimple> colores;
  final List<ItemSimple> tallas;
  final List<ItemSimple> temporadas;
  final List<ItemSimple> colecciones;

  bool get isEmpty =>
      categorias.isEmpty &&
      colores.isEmpty &&
      tallas.isEmpty &&
      temporadas.isEmpty &&
      colecciones.isEmpty;

  factory AuxiliaresCatalogo.fromJson(Map<String, dynamic> json) {
    List<ItemSimple> parseList(dynamic value) {
      if (value is! List) {
        return const [];
      }
      return value
          .whereType<Map>()
          .map((item) => ItemSimple.fromJson(Map<String, dynamic>.from(item)))
          .toList(growable: false);
    }

    return AuxiliaresCatalogo(
      categorias: parseList(json['categorias']),
      colores: parseList(json['colores']),
      tallas: parseList(json['tallas']),
      temporadas: parseList(json['temporadas']),
      colecciones: parseList(json['colecciones']),
    );
  }

  factory AuxiliaresCatalogo.fromPrendas(List<Prenda> prendas) {
    final categorias = <String, ItemSimple>{};
    final colores = <String, ItemSimple>{};
    final tallas = <String, ItemSimple>{};
    final temporadas = <String, ItemSimple>{};
    final colecciones = <String, ItemSimple>{};

    for (final prenda in prendas) {
      if (prenda.categoriaId.isNotEmpty) {
        categorias.putIfAbsent(
          prenda.categoriaId,
          () => ItemSimple(
            id: prenda.categoriaId,
            nombre: prenda.categoriaNombre ?? 'Sin categoria',
          ),
        );
      }
      final temporadaId = prenda.temporadaId;
      if (temporadaId != null && temporadaId.isNotEmpty) {
        temporadas.putIfAbsent(
          temporadaId,
          () => ItemSimple(
            id: temporadaId,
            nombre: prenda.temporadaNombre ?? 'Sin temporada',
          ),
        );
      }
      final coleccionId = prenda.coleccionId;
      if (coleccionId != null && coleccionId.isNotEmpty) {
        colecciones.putIfAbsent(
          coleccionId,
          () => ItemSimple(
            id: coleccionId,
            nombre: prenda.coleccionNombre ?? 'Sin coleccion',
          ),
        );
      }
      for (final variante in prenda.variantes) {
        final tallaNombre = variante.tallaNombre;
        if (tallaNombre != null && tallaNombre.isNotEmpty) {
          tallas.putIfAbsent(
            variante.tallaId.toString(),
            () => ItemSimple(
              id: variante.tallaId.toString(),
              nombre: tallaNombre,
            ),
          );
        }
        final colorNombre = variante.colorNombre;
        if (colorNombre != null && colorNombre.isNotEmpty) {
          colores.putIfAbsent(
            variante.colorId.toString(),
            () => ItemSimple(
              id: variante.colorId.toString(),
              nombre: colorNombre,
              extra: variante.colorHex,
            ),
          );
        }
      }
    }

    List<ItemSimple> sorted(Map<String, ItemSimple> values) {
      final list = values.values.toList();
      list.sort(
        (a, b) => a.nombre.toLowerCase().compareTo(b.nombre.toLowerCase()),
      );
      return list;
    }

    return AuxiliaresCatalogo(
      categorias: sorted(categorias),
      colores: sorted(colores),
      tallas: sorted(tallas),
      temporadas: sorted(temporadas),
      colecciones: sorted(colecciones),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'categorias': categorias
          .map((item) => item.toJson())
          .toList(growable: false),
      'colores': colores.map((item) => item.toJson()).toList(growable: false),
      'tallas': tallas.map((item) => item.toJson()).toList(growable: false),
      'temporadas': temporadas
          .map((item) => item.toJson())
          .toList(growable: false),
      'colecciones': colecciones
          .map((item) => item.toJson())
          .toList(growable: false),
    };
  }
}

class CatalogoFiltros {
  const CatalogoFiltros({
    this.categoriaId,
    this.temporadaId,
    this.coleccionId,
    this.tallaId,
    this.colorId,
    this.precioMin,
    this.precioMax,
    this.genero,
    this.search,
  });

  final String? categoriaId;
  final String? temporadaId;
  final String? coleccionId;
  final int? tallaId;
  final int? colorId;
  final double? precioMin;
  final double? precioMax;
  final String? genero;
  final String? search;

  bool get hasFilters => activeCount > 0;

  int get activeCount {
    var count = 0;
    if (_hasText(categoriaId)) count++;
    if (_hasText(temporadaId)) count++;
    if (_hasText(coleccionId)) count++;
    if (tallaId != null) count++;
    if (colorId != null) count++;
    if (precioMin != null) count++;
    if (precioMax != null) count++;
    if (_hasText(genero)) count++;
    if (_hasText(search)) count++;
    return count;
  }

  static bool _hasText(String? value) =>
      value != null && value.trim().isNotEmpty;

  Map<String, String> toQueryParams(String empresaSlug) {
    final params = <String, String>{'empresa_slug': empresaSlug};
    if (_hasText(categoriaId)) params['categoria_id'] = categoriaId!.trim();
    if (_hasText(temporadaId)) params['temporada_id'] = temporadaId!.trim();
    if (_hasText(coleccionId)) params['coleccion_id'] = coleccionId!.trim();
    if (tallaId != null) params['talla_id'] = tallaId.toString();
    if (colorId != null) params['color_id'] = colorId.toString();
    if (precioMin != null) params['precio_min'] = precioMin.toString();
    if (precioMax != null) params['precio_max'] = precioMax.toString();
    if (_hasText(genero)) params['genero'] = genero!.trim().toLowerCase();
    if (_hasText(search)) params['search'] = search!.trim();
    return params;
  }
}

class CatalogoSnapshot {
  const CatalogoSnapshot({
    required this.version,
    required this.updatedAt,
    required this.items,
  });

  final int version;
  final DateTime updatedAt;
  final List<Prenda> items;
}

class CatalogoResultado {
  const CatalogoResultado({
    required this.items,
    required this.total,
    required this.versionCatalogo,
    required this.isOffline,
    this.sinDatosLocales = false,
    this.cacheUpdatedAt,
  });

  final List<Prenda> items;
  final int total;
  final int versionCatalogo;
  final bool isOffline;
  final bool sinDatosLocales;
  final DateTime? cacheUpdatedAt;
}

List<Prenda> filtrarPrendasLocal(
  List<Prenda> prendas,
  CatalogoFiltros filtros,
) {
  final search = filtros.search?.trim().toLowerCase();
  return prendas
      .where((prenda) {
        if (filtros.categoriaId != null &&
            prenda.categoriaId != filtros.categoriaId) {
          return false;
        }
        if (filtros.temporadaId != null &&
            prenda.temporadaId != filtros.temporadaId) {
          return false;
        }
        if (filtros.coleccionId != null &&
            prenda.coleccionId != filtros.coleccionId) {
          return false;
        }
        if (filtros.genero != null &&
            prenda.genero.toLowerCase() != filtros.genero!.toLowerCase()) {
          return false;
        }
        if (filtros.precioMin != null &&
            prenda.precioBase < filtros.precioMin!) {
          return false;
        }
        if (filtros.precioMax != null &&
            prenda.precioBase > filtros.precioMax!) {
          return false;
        }
        if (filtros.tallaId != null &&
            !prenda.variantes.any((v) => v.tallaId == filtros.tallaId)) {
          return false;
        }
        if (filtros.colorId != null &&
            !prenda.variantes.any((v) => v.colorId == filtros.colorId)) {
          return false;
        }
        if (search != null && search.isNotEmpty) {
          final matches =
              prenda.nombre.toLowerCase().contains(search) ||
              prenda.codigo.toLowerCase().contains(search) ||
              (prenda.marca?.toLowerCase().contains(search) ?? false);
          if (!matches) {
            return false;
          }
        }
        return true;
      })
      .toList(growable: false);
}
