import 'package:fashionstore_mobile/features/auth/data/auth_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('LoginResponse parsea tokens, expiracion y usuario', () {
    final response = LoginResponse.fromJson({
      'access_token': 'access',
      'refresh_token': 'refresh',
      'expires_in': 3600,
      'usuario': {
        'id': 'u-1',
        'empresa_id': 'e-1',
        'nombre': 'Ada Lovelace',
        'correo': 'ada@demo.test',
        'telefono': '70000000',
        'email_verificado': true,
        'estado': 'activo',
        'rol': 'cliente',
        'ultimo_acceso': '2026-10-31T12:00:00Z',
        'created_at': '2026-10-01T12:00:00Z',
      },
    });

    expect(response.accessToken, 'access');
    expect(response.refreshToken, 'refresh');
    expect(response.expiresIn, 3600);
    expect(response.usuario.nombre, 'Ada Lovelace');
    expect(response.usuario.emailVerificado, isTrue);
    expect(response.usuario.ultimoAcceso, isNotNull);
  });

  test('RegisterResponse conserva el token de verificacion demo', () {
    final response = RegisterResponse.fromJson({
      'mensaje': 'Registro creado',
      'usuario_id': 'u-1',
      'empresa_id': 'e-1',
      'email_verificado': false,
      'verification_token': 'token-demo',
    });

    expect(response.mensaje, 'Registro creado');
    expect(response.emailVerificado, isFalse);
    expect(response.verificationToken, 'token-demo');
  });

  test('AppUser tolera campos opcionales ausentes', () {
    final user = AppUser.fromJson({
      'id': 'u-1',
      'nombre': 'Cliente',
      'correo': 'cliente@demo.test',
      'email_verificado': false,
      'estado': 'activo',
      'rol': 'cliente',
    });

    expect(user.telefono, isNull);
    expect(user.ultimoAcceso, isNull);
    expect(user.createdAt, isNull);
  });
}
