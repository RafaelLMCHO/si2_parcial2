import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/session/session_controller.dart';
import '../../common/widgets/password_field.dart';
import '../../common/widgets/session_banners.dart';
import '../data/auth_models.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, required this.session});

  final SessionController session;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _tenantController;
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  RegisterResponse? _response;

  @override
  void initState() {
    super.initState();
    _tenantController = TextEditingController(text: widget.session.tenant);
  }

  @override
  void dispose() {
    _tenantController.dispose();
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    widget.session.clearMessages();
    final response = await widget.session.register(
      empresaSlug: _tenantController.text,
      nombre: _nameController.text,
      correo: _emailController.text,
      telefono: _phoneController.text,
      password: _passwordController.text,
    );
    if (response != null && mounted) {
      setState(() => _response = response);
    }
  }

  void _goToVerification() {
    final response = _response;
    if (response == null) {
      return;
    }
    final tenant = Uri.encodeComponent(_tenantController.text.trim());
    final token = Uri.encodeComponent(response.verificationToken ?? '');
    context.push('/verify-email?empresa_slug=$tenant&token=$token');
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.session,
      builder: (context, _) {
        final session = widget.session;
        final canSubmit = !session.loading && session.isOnline;

        return Scaffold(
          appBar: AppBar(title: const Text('Crear cuenta')),
          body: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 460),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'El registro queda asociado a la empresa indicada.',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.outline,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 14),
                      SessionBanners(session: session),
                      if (_response != null)
                        _RegistrationResult(
                          response: _response!,
                          onVerify: _goToVerification,
                          onBack: () => setState(() => _response = null),
                        )
                      else
                        Card(
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                            side: const BorderSide(color: Color(0xFFE5E7EB)),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Form(
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  TextFormField(
                                    controller: _tenantController,
                                    textInputAction: TextInputAction.next,
                                    decoration: const InputDecoration(
                                      labelText: 'Empresa',
                                      prefixIcon: Icon(
                                        Icons.storefront_outlined,
                                      ),
                                    ),
                                    validator: (value) {
                                      if ((value ?? '').trim().isEmpty) {
                                        return 'Indique el identificador de la empresa.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                  TextFormField(
                                    controller: _nameController,
                                    textInputAction: TextInputAction.next,
                                    autofillHints: const [AutofillHints.name],
                                    decoration: const InputDecoration(
                                      labelText: 'Nombre completo',
                                      prefixIcon: Icon(Icons.person_outline),
                                    ),
                                    validator: (value) {
                                      if ((value ?? '').trim().length < 2) {
                                        return 'Ingrese su nombre.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                  TextFormField(
                                    controller: _emailController,
                                    keyboardType: TextInputType.emailAddress,
                                    textInputAction: TextInputAction.next,
                                    autofillHints: const [AutofillHints.email],
                                    decoration: const InputDecoration(
                                      labelText: 'Correo',
                                      prefixIcon: Icon(Icons.mail_outline),
                                    ),
                                    validator: (value) {
                                      final email = value?.trim() ?? '';
                                      if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
                                          .hasMatch(email)) {
                                        return 'Ingrese un correo valido.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                  TextFormField(
                                    controller: _phoneController,
                                    keyboardType: TextInputType.phone,
                                    textInputAction: TextInputAction.next,
                                    autofillHints: const [
                                      AutofillHints.telephoneNumber,
                                    ],
                                    decoration: const InputDecoration(
                                      labelText: 'Telefono (opcional)',
                                      prefixIcon: Icon(Icons.phone_outlined),
                                    ),
                                  ),
                                  const SizedBox(height: 14),
                                  PasswordField(
                                    controller: _passwordController,
                                    label: 'Contrasena',
                                    autofillHints: const [
                                      AutofillHints.newPassword,
                                    ],
                                    onFieldSubmitted: (_) {
                                      if (canSubmit) {
                                        _submit();
                                      }
                                    },
                                    validator: (value) {
                                      if ((value ?? '').length < 8) {
                                        return 'Minimo 8 caracteres.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 20),
                                  FilledButton(
                                    onPressed: canSubmit ? _submit : null,
                                    child: session.loading
                                        ? const SizedBox(
                                            width: 20,
                                            height: 20,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: Colors.white,
                                            ),
                                          )
                                        : const Text('Registrarme'),
                                  ),
                                  const SizedBox(height: 10),
                                  TextButton(
                                    onPressed: session.loading
                                        ? null
                                        : () => context.go('/login'),
                                    child: const Text(
                                      'Ya tiene cuenta? Iniciar sesion',
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _RegistrationResult extends StatelessWidget {
  const _RegistrationResult({
    required this.response,
    required this.onVerify,
    required this.onBack,
  });

  final RegisterResponse response;
  final VoidCallback onVerify;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final token = response.verificationToken;
    return Card(
      elevation: 0,
      color: const Color(0xFFF0FDF4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFBBF7D0)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(
              Icons.mark_email_read_outlined,
              color: Color(0xFF166534),
              size: 34,
            ),
            const SizedBox(height: 10),
            Text(
              response.mensaje,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF166534), height: 1.45),
            ),
            if (token != null && token.isNotEmpty) ...[
              const SizedBox(height: 14),
              const Text(
                'Token de verificacion (modo demo):',
                style: TextStyle(
                  color: Color(0xFF166534),
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF86EFAC)),
                ),
                child: SelectableText(
                  token,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: Color(0xFF166534),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 16),
            FilledButton(
              onPressed: onVerify,
              child: const Text('Verificar correo'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: onBack,
              child: const Text('Volver al formulario'),
            ),
          ],
        ),
      ),
    );
  }
}
