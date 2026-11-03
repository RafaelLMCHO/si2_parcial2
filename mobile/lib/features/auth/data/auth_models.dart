class AppUser {
  const AppUser({
    required this.id,
    required this.nombre,
    required this.correo,
    required this.emailVerificado,
    required this.estado,
    required this.rol,
    this.empresaId,
    this.telefono,
    this.sucursalId,
    this.ultimoAcceso,
    this.createdAt,
  });

  final String id;
  final String? empresaId;
  final String nombre;
  final String correo;
  final String? telefono;
  final bool emailVerificado;
  final String estado;
  final String rol;
  final String? sucursalId;
  final DateTime? ultimoAcceso;
  final DateTime? createdAt;

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'].toString(),
      empresaId: json['empresa_id']?.toString(),
      nombre: json['nombre']?.toString() ?? '',
      correo: json['correo']?.toString() ?? '',
      telefono: json['telefono']?.toString(),
      emailVerificado: json['email_verificado'] == true,
      estado: json['estado']?.toString() ?? '',
      rol: json['rol']?.toString() ?? '',
      sucursalId: json['sucursal_id']?.toString(),
      ultimoAcceso: DateTime.tryParse(json['ultimo_acceso']?.toString() ?? ''),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'empresa_id': empresaId,
      'nombre': nombre,
      'correo': correo,
      'telefono': telefono,
      'email_verificado': emailVerificado,
      'estado': estado,
      'rol': rol,
      'sucursal_id': sucursalId,
      'ultimo_acceso': ultimoAcceso?.toIso8601String(),
      'created_at': createdAt?.toIso8601String(),
    };
  }
}

class LoginResponse {
  const LoginResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.usuario,
  });

  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final AppUser usuario;

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'].toString(),
      refreshToken: json['refresh_token'].toString(),
      expiresIn: (json['expires_in'] as num?)?.toInt() ?? 0,
      usuario: AppUser.fromJson(json['usuario'] as Map<String, dynamic>),
    );
  }
}

class RefreshResponse {
  const RefreshResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
  });

  final String accessToken;
  final String refreshToken;
  final int expiresIn;

  factory RefreshResponse.fromJson(Map<String, dynamic> json) {
    return RefreshResponse(
      accessToken: json['access_token'].toString(),
      refreshToken: json['refresh_token'].toString(),
      expiresIn: (json['expires_in'] as num?)?.toInt() ?? 0,
    );
  }
}

class RegisterResponse {
  const RegisterResponse({
    required this.mensaje,
    required this.usuarioId,
    required this.empresaId,
    required this.emailVerificado,
    this.verificationToken,
  });

  final String mensaje;
  final String usuarioId;
  final String empresaId;
  final bool emailVerificado;
  final String? verificationToken;

  factory RegisterResponse.fromJson(Map<String, dynamic> json) {
    return RegisterResponse(
      mensaje: json['mensaje']?.toString() ?? '',
      usuarioId: json['usuario_id'].toString(),
      empresaId: json['empresa_id'].toString(),
      emailVerificado: json['email_verificado'] == true,
      verificationToken: json['verification_token']?.toString(),
    );
  }
}

class VerifyEmailResponse {
  const VerifyEmailResponse({required this.mensaje});

  final String mensaje;

  factory VerifyEmailResponse.fromJson(Map<String, dynamic> json) {
    return VerifyEmailResponse(mensaje: json['mensaje']?.toString() ?? '');
  }
}
