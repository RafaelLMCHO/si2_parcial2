import 'package:flutter/material.dart';

import '../../data/catalogo_models.dart';

class FiltrosCatalogoSheet extends StatefulWidget {
  const FiltrosCatalogoSheet({
    super.key,
    required this.initial,
    required this.auxiliares,
  });

  final CatalogoFiltros initial;
  final AuxiliaresCatalogo auxiliares;

  @override
  State<FiltrosCatalogoSheet> createState() => _FiltrosCatalogoSheetState();
}

class _FiltrosCatalogoSheetState extends State<FiltrosCatalogoSheet> {
  late String _categoriaId;
  late String _temporadaId;
  late String _coleccionId;
  late String _genero;
  int? _tallaId;
  int? _colorId;
  late final TextEditingController _precioMinController;
  late final TextEditingController _precioMaxController;

  @override
  void initState() {
    super.initState();
    _categoriaId = widget.initial.categoriaId ?? '';
    _temporadaId = widget.initial.temporadaId ?? '';
    _coleccionId = widget.initial.coleccionId ?? '';
    _genero = widget.initial.genero ?? '';
    _tallaId = widget.initial.tallaId;
    _colorId = widget.initial.colorId;
    _precioMinController = TextEditingController(
      text: _formatInput(widget.initial.precioMin),
    );
    _precioMaxController = TextEditingController(
      text: _formatInput(widget.initial.precioMax),
    );
  }

  @override
  void dispose() {
    _precioMinController.dispose();
    _precioMaxController.dispose();
    super.dispose();
  }

  void _limpiar() {
    setState(() {
      _categoriaId = '';
      _temporadaId = '';
      _coleccionId = '';
      _genero = '';
      _tallaId = null;
      _colorId = null;
      _precioMinController.clear();
      _precioMaxController.clear();
    });
  }

  void _aplicar() {
    final categoriaId = _validId(_categoriaId, widget.auxiliares.categorias);
    final temporadaId = _validId(_temporadaId, widget.auxiliares.temporadas);
    final coleccionId = _validId(_coleccionId, widget.auxiliares.colecciones);
    Navigator.of(context).pop(
      CatalogoFiltros(
        categoriaId: categoriaId.isEmpty ? null : categoriaId,
        temporadaId: temporadaId.isEmpty ? null : temporadaId,
        coleccionId: coleccionId.isEmpty ? null : coleccionId,
        tallaId: _tallaId,
        colorId: _colorId,
        precioMin: _parsePrice(_precioMinController.text),
        precioMax: _parsePrice(_precioMaxController.text),
        genero: _genero.isEmpty ? null : _genero,
        search: widget.initial.search,
      ),
    );
  }

  String _validId(String value, List<ItemSimple> items) {
    if (value.isEmpty) {
      return '';
    }
    return items.any((item) => item.id == value) ? value : '';
  }

  @override
  Widget build(BuildContext context) {
    final aux = widget.auxiliares;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          bottom: MediaQuery.viewInsetsOf(context).bottom + 16,
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Filtrar catalogo',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                  TextButton(onPressed: _limpiar, child: const Text('Limpiar')),
                ],
              ),
              const SizedBox(height: 8),
              _dropdown(
                label: 'Categoria',
                value: _categoriaId,
                items: aux.categorias,
                onChanged: (value) => setState(() => _categoriaId = value),
              ),
              const SizedBox(height: 12),
              _dropdown(
                label: 'Temporada',
                value: _temporadaId,
                items: aux.temporadas,
                onChanged: (value) => setState(() => _temporadaId = value),
              ),
              const SizedBox(height: 12),
              _dropdown(
                label: 'Coleccion',
                value: _coleccionId,
                items: aux.colecciones,
                onChanged: (value) => setState(() => _coleccionId = value),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _genero,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Genero'),
                items: const [
                  DropdownMenuItem(value: '', child: Text('Todos')),
                  DropdownMenuItem(value: 'mujer', child: Text('Mujer')),
                  DropdownMenuItem(value: 'hombre', child: Text('Hombre')),
                  DropdownMenuItem(value: 'nino', child: Text('Nino')),
                  DropdownMenuItem(value: 'unisex', child: Text('Unisex')),
                ],
                onChanged: (value) => setState(() => _genero = value ?? ''),
              ),
              if (aux.tallas.isNotEmpty) ...[
                const SizedBox(height: 18),
                Text('Talla', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: aux.tallas
                      .map((item) {
                        final id = int.tryParse(item.id);
                        if (id == null) {
                          return const SizedBox.shrink();
                        }
                        return FilterChip(
                          label: Text(item.nombre),
                          selected: _tallaId == id,
                          onSelected: (selected) {
                            setState(() => _tallaId = selected ? id : null);
                          },
                        );
                      })
                      .toList(growable: false),
                ),
              ],
              if (aux.colores.isNotEmpty) ...[
                const SizedBox(height: 18),
                Text('Color', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: aux.colores
                      .map((item) {
                        final id = int.tryParse(item.id);
                        if (id == null) {
                          return const SizedBox.shrink();
                        }
                        final color = _parseHexColor(item.extra);
                        return FilterChip(
                          avatar: color == null
                              ? null
                              : CircleAvatar(backgroundColor: color),
                          label: Text(item.nombre),
                          selected: _colorId == id,
                          onSelected: (selected) {
                            setState(() => _colorId = selected ? id : null);
                          },
                        );
                      })
                      .toList(growable: false),
                ),
              ],
              const SizedBox(height: 18),
              Text('Precio', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _precioMinController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Minimo',
                        prefixText: 'Bs ',
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _precioMaxController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Maximo',
                        prefixText: 'Bs ',
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: _aplicar,
                icon: const Icon(Icons.filter_alt_outlined),
                label: const Text('Aplicar filtros'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dropdown({
    required String label,
    required String value,
    required List<ItemSimple> items,
    required ValueChanged<String> onChanged,
  }) {
    final safeValue = _validId(value, items);
    return DropdownButtonFormField<String>(
      initialValue: safeValue,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: [
        const DropdownMenuItem(value: '', child: Text('Todas')),
        ...items.map(
          (item) => DropdownMenuItem(
            value: item.id,
            child: Text(item.nombre, overflow: TextOverflow.ellipsis),
          ),
        ),
      ],
      onChanged: (value) => onChanged(value ?? ''),
    );
  }

  String _formatInput(double? value) {
    if (value == null) {
      return '';
    }
    return value == value.roundToDouble()
        ? value.toStringAsFixed(0)
        : value.toString();
  }

  double? _parsePrice(String raw) {
    final text = raw.trim().replaceAll(',', '.');
    if (text.isEmpty) {
      return null;
    }
    return double.tryParse(text);
  }

  Color? _parseHexColor(String? raw) {
    final text = raw?.trim().replaceFirst('#', '');
    if (text == null || (text.length != 6 && text.length != 8)) {
      return null;
    }
    final value = int.tryParse(text, radix: 16);
    if (value == null) {
      return null;
    }
    return Color(text.length == 6 ? 0xFF000000 | value : value);
  }
}
