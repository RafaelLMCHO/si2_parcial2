# FashionStore Mobile

App Flutter/Dart para Android con CU-01 a CU-04 sobre la API FastAPI del
proyecto.

## Ejecutar

```powershell
# Desde la raiz del repositorio
.\scripts\run_backend.ps1 -BindHost 0.0.0.0
.\scripts\run_mobile.ps1
```

Emulador Android: `API_BASE_URL=http://10.0.2.2:8000/api/v1`.

Dispositivo fisico:

```powershell
.\scripts\run_mobile.ps1 `
  -ApiBaseUrl http://192.168.1.10:8000/api/v1 `
  -Device <device-id>
```

Tambien se puede ejecutar directamente:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

## Pruebas

```powershell
flutter analyze
flutter test
```

## Estructura

| Ruta | Contenido |
|---|---|
| `lib/core` | Configuracion, red, sesion, almacenamiento, tema y router. |
| `lib/features/auth` | Modelos, repositorio y pantallas CU-01/CU-02. |
| `lib/features/profile` | Repositorio y pantalla CU-03/CU-04. |
| `lib/features/common` | Widgets compartidos. |

Los tokens se guardan en `flutter_secure_storage`. SQLite conserva usuario,
tenant, ultima sincronizacion y cola offline. El logout no elimina la cola.

Ver `docs/CU01_CU04_MOVIL.md` para el detalle de arquitectura y offline.
