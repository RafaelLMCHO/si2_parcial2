import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'inventario_controller.dart';

class InventarioScreen extends StatefulWidget {
  final ApiClient apiClient;

  const InventarioScreen({super.key, required this.apiClient});

  @override
  State<InventarioScreen> createState() => _InventarioScreenState();
}

class _InventarioScreenState extends State<InventarioScreen> {
  late final InventarioController _controller;
  final TextEditingController _searchCtrl = TextEditingController();
  bool _soloBajoMinimo = false;

  @override
  void initState() {
    super.initState();
    _controller = InventarioController(widget.apiClient);
    _controller.cargarInventario();
  }

  @override
  void dispose() {
    _controller.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Gestión de Inventario (CU-17)'),
            actions: [
              IconButton(
                icon: Icon(_soloBajoMinimo ? Icons.filter_alt : Icons.filter_alt_outlined),
                tooltip: 'Filtrar bajo mínimo',
                onPressed: () {
                  setState(() => _soloBajoMinimo = !_soloBajoMinimo);
                  _controller.cargarInventario(
                    q: _searchCtrl.text,
                    soloBajoMinimo: _soloBajoMinimo,
                  );
                },
              ),
            ],
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(12.0),
                child: TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: 'Buscar por SKU, prenda o ubicación...',
                    prefixIcon: const Icon(Icons.search),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.arrow_forward),
                      onPressed: () => _controller.cargarInventario(
                        q: _searchCtrl.text,
                        soloBajoMinimo: _soloBajoMinimo,
                      ),
                    ),
                  ),
                  onSubmitted: (val) => _controller.cargarInventario(
                    q: val,
                    soloBajoMinimo: _soloBajoMinimo,
                  ),
                ),
              ),
              if (_controller.loading)
                const Expanded(child: Center(child: CircularProgressIndicator()))
              else if (_controller.error != null)
                Expanded(child: Center(child: Text('Error: ${_controller.error}')))
              else if (_controller.items.isEmpty)
                const Expanded(child: Center(child: Text('No hay existencias registradas.')))
              else
                Expanded(
                  child: ListView.separated(
                    itemCount: _controller.items.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final item = _controller.items[index];
                      final bool bajoMin = (item['cantidad'] ?? 0) <= (item['stock_minimo'] ?? 0);
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: bajoMin ? Colors.red.shade100 : Colors.indigo.shade100,
                          child: Icon(
                            bajoMin ? Icons.warning_amber_rounded : Icons.inventory_2_outlined,
                            color: bajoMin ? Colors.red : Colors.indigo,
                          ),
                        ),
                        title: Text(item['prenda_nombre'] ?? item['sku'] ?? 'Producto'),
                        subtitle: Text(
                          'SKU: ${item['sku']} | Talla: ${item['talla'] ?? '-'} | Color: ${item['color'] ?? '-'}\nSucursal: ${item['sucursal_nombre'] ?? '-'} | Ubic: ${item['ubicacion'] ?? 'Estante Gral'}',
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '${item['cantidad']} uds',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                                color: bajoMin ? Colors.red : Colors.black87,
                              ),
                            ),
                            Text(
                              'Mín: ${item['stock_minimo'] ?? 0}',
                              style: const TextStyle(fontSize: 11, color: Colors.grey),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

