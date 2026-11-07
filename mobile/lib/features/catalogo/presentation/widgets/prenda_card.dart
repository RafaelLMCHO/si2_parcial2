import 'package:flutter/material.dart';

import '../../data/catalogo_models.dart';

class PrendaCard extends StatelessWidget {
  const PrendaCard({super.key, required this.prenda});

  final Prenda prenda;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: SizedBox(
                width: 96,
                height: 116,
                child: _PrendaImage(url: prenda.imagenUrl),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    prenda.nombre,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    [prenda.marca, prenda.categoriaNombre]
                        .where((value) => value != null && value.isNotEmpty)
                        .join(' - '),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: theme.colorScheme.outline),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${prenda.moneda} ${prenda.precioBase.toStringAsFixed(2)}',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: theme.colorScheme.primary,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (prenda.tallasDisponibles.isNotEmpty)
                    Text(
                      'Tallas: ${prenda.tallasDisponibles.join(', ')}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall,
                    ),
                  if (prenda.coloresDisponibles.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 5,
                      runSpacing: 5,
                      children: prenda.coloresDisponibles
                          .take(6)
                          .map((color) => _ColorDot(color: color))
                          .toList(growable: false),
                    ),
                  ],
                  if (prenda.tallasDisponibles.isEmpty &&
                      prenda.coloresDisponibles.isEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Sin variantes registradas',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.outline,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrendaImage extends StatelessWidget {
  const _PrendaImage({required this.url});

  final String? url;

  @override
  Widget build(BuildContext context) {
    final placeholder = Container(
      color: const Color(0xFFF3F4F6),
      alignment: Alignment.center,
      child: Icon(
        Icons.checkroom,
        size: 34,
        color: Theme.of(context).colorScheme.outline,
      ),
    );
    final imageUrl = url;
    if (imageUrl == null || imageUrl.isEmpty) {
      return placeholder;
    }
    return Image.network(
      imageUrl,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) => placeholder,
      loadingBuilder: (context, child, progress) {
        if (progress == null) {
          return child;
        }
        return const ColoredBox(
          color: Color(0xFFF3F4F6),
          child: Center(
            child: SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ),
        );
      },
    );
  }
}

class _ColorDot extends StatelessWidget {
  const _ColorDot({required this.color});

  final ItemSimple color;

  @override
  Widget build(BuildContext context) {
    final parsed = _parseHexColor(color.extra);
    return Tooltip(
      message: color.nombre,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: parsed ?? const Color(0xFFE5E7EB),
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFD1D5DB)),
            ),
          ),
          const SizedBox(width: 3),
          Text(color.nombre, style: Theme.of(context).textTheme.labelSmall),
        ],
      ),
    );
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
