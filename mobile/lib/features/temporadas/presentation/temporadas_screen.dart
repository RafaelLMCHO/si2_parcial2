import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'temporadas_controller.dart';

class TemporadasScreen extends StatefulWidget {
  final ApiClient apiClient;

  const TemporadasScreen({super.key, required this.apiClient});

  @override
  State<TemporadasScreen> createState() => _TemporadasScreenState();
}

class _TemporadasScreenState extends State<TemporadasScreen> {
  late final TemporadasController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TemporadasController(widget.apiClient);
    _controller.cargarTemporadas();
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
            title: const Text('Temporadas y Colecciones (CU-16)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarTemporadas(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.temporadas.isEmpty
                      ? const Center(child: Text('No hay temporadas registradas.'))
                      : ListView.separated(
                          itemCount: _controller.temporadas.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final temp = _controller.temporadas[index];
                            return ListTile(
                              leading: const CircleAvatar(
                                child: Icon(Icons.calendar_today),
                              ),
                              title: Text(temp['nombre'] ?? 'Temporada'),
                              subtitle: Text(
                                'Código: ${temp['codigo']}\n${temp['fecha_inicio'] ?? ''} a ${temp['fecha_fin'] ?? ''}',
                              ),
                              trailing: Chip(
                                label: Text(temp['activo'] == true ? 'Vigente' : 'Inactiva'),
                                backgroundColor: temp['activo'] == true ? Colors.green.shade50 : Colors.grey.shade200,
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}

