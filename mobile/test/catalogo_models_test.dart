import 'package:fashionstore_mobile/features/catalogo/data/catalogo_models.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _prendaJson({
  String id = 'p-1',
  String nombre = 'Vestido floral',
  String marca = 'Aurora',
  String categoriaId = 'cat-1',
  String categoriaNombre = 'Vestidos',
  String genero = 'mujer',
  num precioBase = 199.90,
  String? temporadaId = 'temp-1',
  String? temporadaNombre = 'Verano',
  String? coleccionId = 'col-1',
  String? coleccionNombre = 'Solar',
  int tallaId = 2,
  int colorId = 5,
}) {
  return {
    'id': id,
    'empresa_id': 'e-1',
    'codigo': 'COD-$id',
    'nombre': nombre,
    'marca': marca,
    'genero': genero,
    'precio_base': precioBase.toString(),
    'moneda': 'BOB',
    'categoria_id': categoriaId,
    'categoria_nombre': categoriaNombre,
    'temporada_id': temporadaId,
    'temporada_nombre': temporadaNombre,
    'coleccion_id': coleccionId,
    'coleccion_nombre': coleccionNombre,
    'estado': 'activa',
    'variantes': [
      {
        'id': 'v-1',
        'prenda_id': id,
        'talla_id': tallaId,
        'talla_nombre': 'M',
        'color_id': colorId,
        'color_nombre': 'Rojo',
        'color_hex': '#FF0000',
        'sku': 'SKU-$id-M-ROJO',
        'precio_venta': '210.50',
        'costo': '100.00',
        'estado': 'activa',
      },
      {
        'id': 'v-2',
        'prenda_id': id,
        'talla_id': tallaId + 1,
        'talla_nombre': 'L',
        'color_id': colorId + 1,
        'color_nombre': 'Azul',
        'color_hex': '#0000FF',
        'sku': 'SKU-$id-L-AZUL',
        'precio_venta': '220.00',
        'costo': '105.00',
        'estado': 'activa',
      },
    ],
  };
}

void main() {
  test('Prenda parsea precios Decimal y variantes', () {
    final prenda = Prenda.fromJson(_prendaJson());

    expect(prenda.id, 'p-1');
    expect(prenda.precioBase, 199.90);
    expect(prenda.moneda, 'BOB');
    expect(prenda.variantes, hasLength(2));
    expect(prenda.variantes.first.precioVenta, 210.50);
    expect(prenda.tallasDisponibles, containsAll(['M', 'L']));
    expect(prenda.coloresDisponibles.map((c) => c.nombre), contains('Rojo'));
  });

  test('PrendaListResponse expone total y version del catalogo', () {
    final response = PrendaListResponse.fromJson({
      'total': 1,
      'version_catalogo': 12,
      'items': [_prendaJson()],
    });

    expect(response.total, 1);
    expect(response.versionCatalogo, 12);
    expect(response.items.single.nombre, 'Vestido floral');
  });

  test('AuxiliaresCatalogo se derivan de las prendas cacheadas', () {
    final prendas = [
      Prenda.fromJson(_prendaJson()),
      Prenda.fromJson(
        _prendaJson(
          id: 'p-2',
          nombre: 'Camisa',
          categoriaId: 'cat-2',
          categoriaNombre: 'Camisas',
          genero: 'hombre',
          temporadaId: null,
          temporadaNombre: null,
          coleccionId: null,
          coleccionNombre: null,
        ),
      ),
    ];

    final auxiliares = AuxiliaresCatalogo.fromPrendas(prendas);

    expect(auxiliares.categorias, hasLength(2));
    expect(auxiliares.temporadas.single.nombre, 'Verano');
    expect(auxiliares.colecciones.single.nombre, 'Solar');
    expect(auxiliares.tallas.map((t) => t.nombre), containsAll(['M', 'L']));
    expect(
      auxiliares.colores.map((c) => c.nombre),
      containsAll(['Rojo', 'Azul']),
    );
  });

  test('toQueryParams incluye solo filtros activos y normaliza genero', () {
    final params = const CatalogoFiltros(
      categoriaId: 'cat-1',
      tallaId: 2,
      precioMin: 100,
      genero: 'Mujer',
      search: ' vestido ',
    ).toQueryParams('demo');

    expect(params['empresa_slug'], 'demo');
    expect(params['categoria_id'], 'cat-1');
    expect(params['talla_id'], '2');
    expect(params['precio_min'], '100.0');
    expect(params['genero'], 'mujer');
    expect(params['search'], 'vestido');
    expect(params.containsKey('color_id'), isFalse);
  });

  test('filtrarPrendasLocal aplica combinacion de filtros', () {
    final prendas = [
      Prenda.fromJson(_prendaJson()),
      Prenda.fromJson(
        _prendaJson(
          id: 'p-2',
          nombre: 'Camisa casual',
          marca: 'Norte',
          categoriaId: 'cat-2',
          categoriaNombre: 'Camisas',
          genero: 'hombre',
          precioBase: 80,
          temporadaId: 'temp-2',
          temporadaNombre: 'Invierno',
          coleccionId: null,
          coleccionNombre: null,
          tallaId: 4,
          colorId: 7,
        ),
      ),
    ];

    expect(
      filtrarPrendasLocal(prendas, const CatalogoFiltros(categoriaId: 'cat-1')),
      hasLength(1),
    );
    expect(
      filtrarPrendasLocal(
        prendas,
        const CatalogoFiltros(genero: 'HOMBRE'),
      ).single.id,
      'p-2',
    );
    expect(
      filtrarPrendasLocal(
        prendas,
        const CatalogoFiltros(tallaId: 3, colorId: 6),
      ).single.id,
      'p-1',
    );
    expect(
      filtrarPrendasLocal(
        prendas,
        const CatalogoFiltros(precioMin: 90, precioMax: 210),
      ).single.id,
      'p-1',
    );
    expect(
      filtrarPrendasLocal(
        prendas,
        const CatalogoFiltros(search: 'camisa'),
      ).single.id,
      'p-2',
    );
    expect(
      filtrarPrendasLocal(
        prendas,
        const CatalogoFiltros(temporadaId: 'temp-1', coleccionId: 'col-1'),
      ).single.id,
      'p-1',
    );
  });

  test('activeCount cuenta busqueda y filtros seleccionados', () {
    expect(const CatalogoFiltros().activeCount, 0);
    expect(
      const CatalogoFiltros(
        categoriaId: 'cat-1',
        tallaId: 2,
        precioMax: 200,
        search: 'vestido',
      ).activeCount,
      4,
    );
  });
}
