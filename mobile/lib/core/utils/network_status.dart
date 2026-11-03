import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

class NetworkStatus extends ValueNotifier<bool> {
  NetworkStatus() : super(true);

  final Connectivity _connectivity = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _subscription;

  Future<void> init() async {
    final results = await _connectivity.checkConnectivity();
    value = _hasConnection(results);
    _subscription = _connectivity.onConnectivityChanged.listen((results) {
      value = _hasConnection(results);
    });
  }

  void markOnline() {
    value = true;
  }

  void markOffline() {
    value = false;
  }

  bool _hasConnection(List<ConnectivityResult> results) {
    return results.any((result) => result != ConnectivityResult.none);
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }
}
