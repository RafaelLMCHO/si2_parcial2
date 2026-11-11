import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../../controller/cu25_descargar_catalogo_offline_controller.dart';

class CatalogoOfflineScreen extends StatefulWidget {
  final ApiClient apiClient;
  final LocalDatabase database;
  final SessionController? session;

  const CatalogoOfflineScreen({
    super.key,
    required this.apiClient,
    required this.database,
    this.session,
  });

  @override
  State<CatalogoOfflineScreen> createState() => _CatalogoOfflineScreenState();
}

class _CatalogoOfflineScreenState extends State<CatalogoOfflineScreen> {
  late final CU25DescargarCatalogoOfflineController _controller;

  @override
  void initState() {
    super.initState();
    _controller = CU25DescargarCatalogoOfflineController(widget.apiClient, widget.database);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Descargar Catálogo Offline (CU-25)'),
          ),
          body: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Persistencia Local SQLite / IndexedDB', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        SizedBox(height: 8),
                        Text('Permite empaquetar prendas, variantes y existencias en el almacenamiento local para operar en contingencia sin conexión a Internet.'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                if (_controller.ultimaDescarga != null) ...[
                  Text('Última descarga: ${_controller.ultimaDescarga}'),
                  Text('Sucursales almacenadas: ${_controller.sucursalesDescargadas}'),
                  Text('Artículos almacenados: ${_controller.articulosDescargados}'),
                  const SizedBox(height: 16),
                ],
                if (_controller.error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
                    child: Text(_controller.error!, style: TextStyle(color: Colors.red.shade800)),
                  ),
                const Spacer(),
                ElevatedButton.icon(
                  onPressed: _controller.loading
                      ? null
                      : () => _controller.descargarCatalogo(
                          empresaSlug: widget.session?.tenant,
                        ),
                  icon: _controller.loading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.download),
                  label: Text(_controller.loading ? 'Descargando paquete gzip...' : 'Actualizar Catálogo Offline Ahora'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

