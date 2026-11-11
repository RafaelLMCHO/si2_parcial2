import 'package:flutter/material.dart';

const String kFallbackPrendaImageUrl =
    'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';

String _normalizeText(String? input) {
  return (input ?? '')
      .trim()
      .toLowerCase()
      .replaceAll('á', 'a')
      .replaceAll('é', 'e')
      .replaceAll('í', 'i')
      .replaceAll('ó', 'o')
      .replaceAll('ú', 'u')
      .replaceAll('ñ', 'n');
}

String resolvePrendaImageUrl({
  String? imagenUrl,
  String? nombre,
  String? categoriaNombre,
}) {
  final rawUrl = imagenUrl?.trim() ?? '';
  if (rawUrl.isNotEmpty &&
      rawUrl.startsWith('http') &&
      !rawUrl.contains('cdn.fashionstore.test')) {
    return rawUrl;
  }

  final n = _normalizeText(nombre);
  final c = _normalizeText(categoriaNombre);

  if (n.contains('camisa') || n.contains('lino') || c.contains('camisa')) {
    return 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80';
  }
  if (n.contains('blazer') || n.contains('traje') || c.contains('chaqueta')) {
    return 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=600&q=80';
  }
  if (n.contains('pijama') || c.contains('interior')) {
    return 'https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80';
  }
  if (n.contains('vestido') || c.contains('vestido')) {
    return 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80';
  }
  if (n.contains('pantalon') || n.contains('jean') || c.contains('pantalon')) {
    return 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80';
  }
  if (c.contains('calzado') ||
      n.contains('zapato') ||
      n.contains('zapatilla')) {
    return 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80';
  }
  if (c.contains('deportiv') || n.contains('deportiv')) {
    return 'https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80';
  }
  if (c.contains('accesorio')) {
    return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80';
  }

  return kFallbackPrendaImageUrl;
}

class PrendaNetworkImage extends StatelessWidget {
  const PrendaNetworkImage({
    super.key,
    this.imagenUrl,
    this.nombre,
    this.categoriaNombre,
    this.fit = BoxFit.cover,
    this.iconSize = 34,
  });

  final String? imagenUrl;
  final String? nombre;
  final String? categoriaNombre;
  final BoxFit fit;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    final resolvedUrl = resolvePrendaImageUrl(
      imagenUrl: imagenUrl,
      nombre: nombre,
      categoriaNombre: categoriaNombre,
    );

    final placeholder = Container(
      color: const Color(0xFFF3F4F6),
      alignment: Alignment.center,
      child: Icon(
        Icons.checkroom,
        size: iconSize,
        color: Theme.of(context).colorScheme.outline,
      ),
    );

    return Image.network(
      resolvedUrl,
      fit: fit,
      errorBuilder: (context, error, stackTrace) {
        if (resolvedUrl == kFallbackPrendaImageUrl) {
          return placeholder;
        }
        return Image.network(
          kFallbackPrendaImageUrl,
          fit: fit,
          errorBuilder: (_, _, _) => placeholder,
        );
      },
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

