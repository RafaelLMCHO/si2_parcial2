import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/session/session_controller.dart';
import '../../common/widgets/session_banners.dart';

class VerifyEmailScreen extends StatefulWidget {
  const VerifyEmailScreen({
    super.key,
    required this.session,
    required this.initialTenant,
    required this.initialToken,
  });

  final SessionController session;
  final String initialTenant;
  final String initialToken;

  @override
  State<VerifyEmailScreen> createState() => _VerifyEmailScreenState();
}

class _VerifyEmailScreenState extends State<VerifyEmailScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _tenantController;
  late final TextEditingController _tokenController;
  String? _successMessage;

  @override
  void initState() {
    super.initState();
    _tenantController = TextEditingController(text: widget.initialTenant);
    _tokenController = TextEditingController(text: widget.initialToken);
  }

  @override
  void dispose() {
    _tenantController.dispose();
    _tokenController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    widget.session.clearMessages();
    final response = await widget.session.verifyEmail(
      empresaSlug: _tenantController.text,
      token: _tokenController.text,
    );
    if (response != null && mounted) {
      setState(() => _successMessage = response.mensaje);
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
          appBar: AppBar(title: const Text('Verificar correo')),
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
                        'Confirme el token enviado a su correo para activar el acceso.',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.outline,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 14),
                      SessionBanners(session: session),
                      if (_successMessage != null)
                        Card(
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
                                  Icons.verified_outlined,
                                  color: Color(0xFF166534),
                                  size: 34,
                                ),
                                const SizedBox(height: 10),
                                Text(
                                  _successMessage!,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(
                                    color: Color(0xFF166534),
                                    height: 1.45,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                FilledButton(
                                  onPressed: () => context.go('/login'),
                                  child: const Text('Ir a iniciar sesion'),
                                ),
                              ],
                            ),
                          ),
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
                                        return 'Indique la empresa.';
                                      }
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                  TextFormField(
                                    controller: _tokenController,
                                    minLines: 1,
                                    maxLines: 3,
                                    decoration: const InputDecoration(
                                      labelText: 'Token de verificacion',
                                      alignLabelWithHint: true,
                                      prefixIcon: Icon(Icons.key_outlined),
                                    ),
                                    validator: (value) {
                                      if ((value ?? '').trim().length < 20) {
                                        return 'Ingrese el token completo.';
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
                                        : const Text('Verificar'),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      const SizedBox(height: 10),
                      TextButton(
                        onPressed: () => context.go('/login'),
                        child: const Text('Volver a iniciar sesion'),
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
