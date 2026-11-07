class DisponibilidadVariante {
  final String varianteId;
  final String sku;
  final String talla;
  final String color;
  final int stockDisponible;

  DisponibilidadVariante({
    required this.varianteId,
    required this.sku,
    required this.talla,
    required this.color,
    required this.stockDisponible,
  });

  factory DisponibilidadVariante.fromJson(Map<String, dynamic> json) {
    return DisponibilidadVariante(
      varianteId: json['variante_id'] ?? '',
      sku: json['sku'] ?? '',
      talla: json['talla'] ?? '',
      color: json['color'] ?? '',
      stockDisponible: json['stock_disponible'] ?? 0,
    );
  }
}

class DisponibilidadSucursal {
  final String sucursalId;
  final String nombre;
  final String direccion;
  final String ciudad;
  final List<DisponibilidadVariante> variantes;

  DisponibilidadSucursal({
    required this.sucursalId,
    required this.nombre,
    required this.direccion,
    required this.ciudad,
    required this.variantes,
  });

  factory DisponibilidadSucursal.fromJson(Map<String, dynamic> json) {
    return DisponibilidadSucursal(
      sucursalId: json['sucursal_id'] ?? '',
      nombre: json['nombre'] ?? '',
      direccion: json['direccion'] ?? '',
      ciudad: json['ciudad'] ?? '',
      variantes: (json['variantes'] as List<dynamic>? ?? [])
          .map((v) => DisponibilidadVariante.fromJson(v))
          .toList(),
    );
  }
}

class DisponibilidadPrenda {
  final String prendaId;
  final bool agotadoEnTodas;
  final String actualizadoEn;
  final List<DisponibilidadSucursal> sucursales;
  final bool esLocal;

  DisponibilidadPrenda({
    required this.prendaId,
    required this.agotadoEnTodas,
    required this.actualizadoEn,
    required this.sucursales,
    this.esLocal = false,
  });

  factory DisponibilidadPrenda.fromJson(Map<String, dynamic> json, {bool esLocal = false}) {
    return DisponibilidadPrenda(
      prendaId: json['prenda_id'] ?? '',
      agotadoEnTodas: json['agotado_en_todas'] ?? false,
      actualizadoEn: json['actualizado_en'] ?? '',
      sucursales: (json['sucursales'] as List<dynamic>? ?? [])
          .map((s) => DisponibilidadSucursal.fromJson(s))
          .toList(),
      esLocal: esLocal,
    );
  }
}

