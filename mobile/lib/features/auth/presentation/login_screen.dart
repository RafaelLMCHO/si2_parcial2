import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/session/session_controller.dart';
import '../../common/widgets/password_field.dart';
import '../../common/widgets/session_banners.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.session});

  final SessionController session;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _tenantController;
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tenantController = TextEditingController(text: widget.session.tenant);
  }

  @override
  void dispose() {
    _tenantController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    widget.session.clearMessages();
    final success = await widget.session.login(
      empresaSlug: _tenantController.text,
      correo: _emailController.text,
      password: _passwordController.text,
    );
    if (success && mounted) {
      context.go('/profile');
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.session,
      builder: (context, _) {
        final session = widget.session;
        final canSubmit = !session.loading && session.isOnline;

        return Scaffold(
          body: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 460),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const _BrandHeader(
                        title: 'Iniciar sesion',
                        subtitle: 'Acceda con su empresa, correo y contrasena.',
                      ),
                      SessionBanners(session: session),
                      Card(
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                          side: const BorderSide(color: Color(0xFFE5E7EB)),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: AutofillGroup(
                            child: Form(
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  TextFormField(
                                    controller: _tenantController,
                                    textInputAction: TextInputAction.next,
                                    autofillHints: const [
                                      AutofillHints.organizationName,
                                    ],
                                    decoration: const InputDecoration(
                                      labelText: 'Empresa',
                                      helperText:
                                          'Deje vacio solo para superadmin.',
                                      prefixIcon: Icon(
                                        Icons.storefront_outlined,
                                      ),
                                    ),
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
                                      if (email.isEmpty) {
                                        return 'Ingrese su correo.';
                                      }
                                      if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
                                          .hasMatch(email)) {
                                        return 'Ingrese un correo valido.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                  PasswordField(
                                    controller: _passwordController,
                                    label: 'Contrasena',
                                    autofillHints: const [
                                      AutofillHints.password,
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
                                        : const Text('Ingresar'),
                                  ),
                                  if (!session.isOnline)
                                    const Padding(
                                      padding: EdgeInsets.only(top: 10),
                                      child: Text(
                                        'El inicio de sesion necesita conexion.',
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          color: Color(0xFF92400E),
                                          fontSize: 12,
                                        ),
                                      ),
                                    ),
                                  const SizedBox(height: 12),
                                  TextButton(
                                    onPressed: session.loading
                                        ? null
                                        : () => context.push('/register'),
                                    child: const Text(
                                      'No tiene cuenta? Registrarse',
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'FashionStore SaaS - Sistemas de Informacion II',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.outline,
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

class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 8, 4, 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: const Text(
                  'FS',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              const Text(
                'FashionStore',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Text(title, style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: TextStyle(
              color: Theme.of(context).colorScheme.outline,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}
