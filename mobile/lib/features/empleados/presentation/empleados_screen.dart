import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'empleados_controller.dart';

class EmpleadosScreen extends StatefulWidget {
  final ApiClient apiClient;

  const EmpleadosScreen({super.key, required this.apiClient});

  @override
  State<EmpleadosScreen> createState() => _EmpleadosScreenState();
}

class _EmpleadosScreenState extends State<EmpleadosScreen> {
  late final EmpleadosController _controller;

  @override
  void initState() {
    super.initState();
    _controller = EmpleadosController(widget.apiClient);
    _controller.cargarEmpleados();
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
            title: const Text('Gestión de Empleados (CU-10)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarEmpleados(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.empleados.isEmpty
                      ? const Center(child: Text('No hay empleados registrados.'))
                      : ListView.separated(
                          itemCount: _controller.empleados.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final emp = _controller.empleados[index];
                            return ListTile(
                              leading: CircleAvatar(
                                child: Text((emp['nombre'] as String? ?? 'E')[0].toUpperCase()),
                              ),
                              title: Text(emp['nombre'] ?? 'Empleado'),
                              subtitle: Text('${emp['email']} • Rol: ${emp['rol'] ?? 'vendedor'}'),
                              trailing: Chip(
                                label: Text(emp['activo'] == true ? 'Activo' : 'Inactivo'),
                                backgroundColor: emp['activo'] == true ? Colors.green.shade50 : Colors.red.shade50,
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}

