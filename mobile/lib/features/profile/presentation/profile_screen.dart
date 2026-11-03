import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/session/session_controller.dart';
import '../../auth/data/auth_models.dart';
import '../../common/widgets/password_field.dart';
import '../../common/widgets/session_banners.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.session});

  final SessionController session;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _profileKey = GlobalKey<FormState>();
  final _passwordKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();

  String? _syncedId;
  String? _syncedName;
  String? _syncedPhone;

  @override
  void initState() {
    super.initState();
    _syncForms(widget.session.user);
    widget.session.addListener(_onSessionChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.session.isOnline) {
        widget.session.refreshProfile();
      }
    });
  }

  @override
  void dispose() {
    widget.session.removeListener(_onSessionChanged);
    _nameController.dispose();
    _phoneController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  void _onSessionChanged() {
    _syncForms(widget.session.user);
  }

  void _syncForms(AppUser? user) {
    if (user == null) {
      return;
    }
    if (_syncedId == user.id &&
        _syncedName == user.nombre &&
        _syncedPhone == (user.telefono ?? '')) {
      return;
    }
    _syncedId = user.id;
    _syncedName = user.nombre;
    _syncedPhone = user.telefono ?? '';
    _nameController.text = user.nombre;
    _phoneController.text = user.telefono ?? '';
  }

  Future<void> _saveProfile() async {
    if (!_profileKey.currentState!.validate()) {
      return;
    }
    widget.session.clearMessages();
    await widget.session.updateProfile(
      nombre: _nameController.text,
      telefono: _phoneController.text.trim().isEmpty
          ? null
          : _phoneController.text.trim(),
    );
  }

  Future<void> _changePassword() async {
    if (!_passwordKey.currentState!.validate()) {
      return;
    }
    widget.session.clearMessages();
    final success = await widget.session.changePassword(
      passwordActual: _currentPasswordController.text,
      passwordNueva: _newPasswordController.text,
    );
    if (success) {
      _currentPasswordController.clear();
      _newPasswordController.clear();
    }
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          widget.session.pendingOperations > 0
              ? 'Hay operaciones pendientes'
              : 'Desea salir?',
        ),
        content: Text(
          widget.session.pendingOperations > 0
              ? 'Las operaciones pendientes de sincronizar se conservaran en este dispositivo.'
              : 'Se cerrara su sesion en este dispositivo.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Cerrar sesion'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await widget.session.logout();
      if (mounted) {
        context.go('/login');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.session,
      builder: (context, _) {
        final session = widget.session;
        final user = session.user;
        final canWrite = session.canWrite && !session.loading;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Mi perfil'),
            actions: [
              IconButton(
                tooltip: 'Cerrar sesion',
                onPressed: _confirmLogout,
                icon: const Icon(Icons.logout),
              ),
            ],
          ),
          body: SafeArea(
            child: RefreshIndicator(
              onRefresh: session.refreshProfile,
              child: ListView(
                padding: const EdgeInsets.all(16),
                physics: const AlwaysScrollableScrollPhysics(),
                children: [
                  SessionBanners(session: session),
                  if (user == null)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: Text('No hay datos de perfil disponibles.'),
                      ),
                    )
                  else ...[
                    _ProfileHero(user: user, tenant: session.tenant),
                    const SizedBox(height: 12),
                    if (session.pendingOperations > 0)
                      const _WarningCard(
                        text: 'Hay operaciones pendientes en la cola offline. Cerrar sesion no las elimina.',
                      ),
                    if (session.pendingOperations > 0)
                      const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Datos personales',
                      child: Form(
                        key: _profileKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            TextFormField(
                              controller: _nameController,
                              enabled: canWrite,
                              textInputAction: TextInputAction.next,
                              autofillHints: const [AutofillHints.name],
                              decoration: const InputDecoration(
                                labelText: 'Nombre',
                                prefixIcon: Icon(Icons.person_outline),
                              ),
                              validator: (value) {
                                if ((value ?? '').trim().length < 2) {
                                  return 'Ingrese su nombre.';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _phoneController,
                              enabled: canWrite,
                              keyboardType: TextInputType.phone,
                              autofillHints: const [
                                AutofillHints.telephoneNumber,
                              ],
                              decoration: const InputDecoration(
                                labelText: 'Telefono',
                                prefixIcon: Icon(Icons.phone_outlined),
                              ),
                            ),
                            const SizedBox(height: 16),
                            FilledButton(
                              onPressed: canWrite ? _saveProfile : null,
                              child: session.loading
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Text('Guardar cambios'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Seguridad',
                      child: Form(
                        key: _passwordKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            PasswordField(
                              controller: _currentPasswordController,
                              label: 'Contrasena actual',
                              enabled: canWrite,
                              autofillHints: const [AutofillHints.password],
                              textInputAction: TextInputAction.next,
                              validator: (value) {
                                if ((value ?? '').isEmpty) {
                                  return 'Ingrese su contrasena actual.';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            PasswordField(
                              controller: _newPasswordController,
                              label: 'Nueva contrasena',
                              enabled: canWrite,
                              autofillHints: const [AutofillHints.newPassword],
                              onFieldSubmitted: (_) {
                                if (canWrite) {
                                  _changePassword();
                                }
                              },
                              validator: (value) {
                                if ((value ?? '').length < 8) {
                                  return 'Minimo 8 caracteres.';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            FilledButton(
                              onPressed: canWrite ? _changePassword : null,
                              child: const Text('Cambiar contrasena'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Estado de la cuenta',
                      child: Column(
                        children: [
                          _InfoRow(
                            label: 'Correo verificado',
                            value: user.emailVerificado ? 'Si' : 'No',
                          ),
                          _InfoRow(label: 'Estado', value: user.estado),
                          _InfoRow(
                            label: 'Ultimo acceso',
                            value: _formatDate(user.ultimoAcceso),
                          ),
                          _InfoRow(
                            label: 'Alta',
                            value: _formatDate(user.createdAt),
                          ),
                          _InfoRow(
                            label: 'Ultima sincronizacion',
                            value: _formatDate(session.lastSync),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  String _formatDate(DateTime? value) {
    if (value == null) {
      return 'Sin registro';
    }
    return DateFormat('dd/MM/yyyy HH:mm').format(value.toLocal());
  }
}

class _ProfileHero extends StatelessWidget {
  const _ProfileHero({required this.user, required this.tenant});

  final AppUser user;
  final String tenant;

  @override
  Widget build(BuildContext context) {
    final trimmedName = user.nombre.trim();
    final initial = trimmedName.isEmpty
        ? '?'
        : trimmedName.substring(0, 1).toUpperCase();
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Colors.white,
              child: Text(
                initial,
                style: const TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user.nombre,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    user.correo,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      _Chip(label: 'Rol ${user.rol}'),
                      _Chip(label: 'Empresa $tenant'),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFFDF2F8),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: Theme.of(context).colorScheme.primary,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              label,
              style: TextStyle(color: Theme.of(context).colorScheme.outline),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _WarningCard extends StatelessWidget {
  const _WarningCard({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFDE68A)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.sync_problem, color: Color(0xFF92400E), size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Color(0xFF92400E), height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}
