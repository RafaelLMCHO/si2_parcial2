package com.fashionstore.fashionstore_mobile

import android.Manifest
import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Base64
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream

class MainActivity : FlutterActivity() {
    companion object {
        private const val VOICE_CHANNEL = "fashionstore/voice"
        private const val FILES_CHANNEL = "fashionstore/files"
        private const val REQ_RECORD_AUDIO = 3401
        private const val REQ_SPEECH_DIALOG = 3402
    }

    private var voiceChannel: MethodChannel? = null
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false
    private var pendingLocale: String = "es-BO"
    private var pendingStartAfterPermission = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        voiceChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, VOICE_CHANNEL).apply {
            setMethodCallHandler { call, result ->
                when (call.method) {
                    "isAvailable" -> {
                        val available = SpeechRecognizer.isRecognitionAvailable(this@MainActivity) ||
                            canLaunchSpeechDialog()
                        result.success(available)
                    }
                    "startListening" -> {
                        val locale = call.argument<String>("locale")?.takeIf { it.isNotBlank() } ?: "es-BO"
                        handleStartListening(locale)
                        result.success(null)
                    }
                    "stopListening" -> {
                        stopSpeechRecognition()
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
        }

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, FILES_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "saveExportFile" -> {
                        val fileName = call.argument<String>("fileName")
                        val mimeType = call.argument<String>("mimeType") ?: "application/octet-stream"
                        val contentBase64 = call.argument<String>("base64")
                        if (fileName.isNullOrBlank() || contentBase64.isNullOrBlank()) {
                            result.error("INVALID_ARGS", "Faltan datos del archivo a guardar.", null)
                            return@setMethodCallHandler
                        }
                        try {
                            val bytes = Base64.decode(contentBase64, Base64.DEFAULT)
                            val savedLocation = saveToDownloads(fileName, mimeType, bytes)
                            result.success(savedLocation)
                        } catch (e: Exception) {
                            result.error(
                                "SAVE_ERROR",
                                e.localizedMessage ?: "No se pudo guardar el reporte en el dispositivo.",
                                null
                            )
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun canLaunchSpeechDialog(): Boolean {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        return intent.resolveActivity(packageManager) != null
    }

    private fun hasAudioPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun handleStartListening(locale: String) {
        pendingLocale = locale
        if (!hasAudioPermission() && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            pendingStartAfterPermission = true
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQ_RECORD_AUDIO)
            return
        }
        startSpeechRecognition(locale)
    }

    private fun startSpeechRecognition(locale: String) {
        runOnUiThread {
            if (!SpeechRecognizer.isRecognitionAvailable(this)) {
                launchSpeechDialogFallback(locale)
                return@runOnUiThread
            }

            try {
                speechRecognizer?.destroy()
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
                    setRecognitionListener(object : RecognitionListener {
                        override fun onReadyForSpeech(params: Bundle?) {
                            isListening = true
                            emitVoiceEvent("onListeningChanged", true)
                        }

                        override fun onBeginningOfSpeech() {}
                        override fun onRmsChanged(rmsdB: Float) {}
                        override fun onBufferReceived(buffer: ByteArray?) {}
                        override fun onEndOfSpeech() {
                            isListening = false
                            emitVoiceEvent("onListeningChanged", false)
                        }

                        override fun onError(error: Int) {
                            isListening = false
                            emitVoiceEvent("onListeningChanged", false)
                            if (error == SpeechRecognizer.ERROR_CLIENT && !canLaunchSpeechDialog()) {
                                emitVoiceEvent(
                                    "onError",
                                    "El reconocimiento de voz no está disponible en este dispositivo."
                                )
                                return
                            }
                            emitVoiceEvent("onError", mapSpeechError(error))
                        }

                        override fun onResults(results: Bundle?) {
                            isListening = false
                            emitVoiceEvent("onListeningChanged", false)
                            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                            val recognized = matches?.firstOrNull()?.trim().orEmpty()
                            if (recognized.isNotEmpty()) {
                                emitVoiceEvent("onFinalResult", recognized)
                            } else {
                                emitVoiceEvent(
                                    "onError",
                                    "No se entendió ninguna frase. Intenta nuevamente."
                                )
                            }
                        }

                        override fun onPartialResults(partialResults: Bundle?) {
                            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                            val partial = matches?.firstOrNull()?.trim().orEmpty()
                            if (partial.isNotEmpty()) {
                                emitVoiceEvent("onPartialResult", partial)
                            }
                        }

                        override fun onEvent(eventType: Int, params: Bundle?) {}
                    })
                }

                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(
                        RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                    )
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, locale)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "es-ES")
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                }

                isListening = true
                emitVoiceEvent("onListeningChanged", true)
                speechRecognizer?.startListening(intent)
            } catch (e: Exception) {
                isListening = false
                emitVoiceEvent("onListeningChanged", false)
                launchSpeechDialogFallback(locale)
            }
        }
    }

    @Suppress("DEPRECATION")
    private fun launchSpeechDialogFallback(locale: String) {
        if (!canLaunchSpeechDialog()) {
            emitVoiceEvent("onListeningChanged", false)
            emitVoiceEvent(
                "onError",
                "Tu dispositivo no tiene un servicio de reconocimiento de voz instalado (puedes escribir la consulta directamente)."
            )
            return
        }
        try {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                )
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, locale)
                putExtra(RecognizerIntent.EXTRA_PROMPT, "Habla tu consulta de reporte en español...")
            }
            isListening = true
            emitVoiceEvent("onListeningChanged", true)
            startActivityForResult(intent, REQ_SPEECH_DIALOG)
        } catch (e: Exception) {
            isListening = false
            emitVoiceEvent("onListeningChanged", false)
            emitVoiceEvent(
                "onError",
                "No se pudo abrir el dictado por voz en este dispositivo."
            )
        }
    }

    private fun stopSpeechRecognition() {
        runOnUiThread {
            if (isListening) {
                try {
                    speechRecognizer?.stopListening()
                } catch (_: Exception) {
                }
                isListening = false
                emitVoiceEvent("onListeningChanged", false)
            }
        }
    }

    private fun emitVoiceEvent(method: String, argument: Any?) {
        runOnUiThread {
            voiceChannel?.invokeMethod(method, argument)
        }
    }

    private fun mapSpeechError(code: Int): String = when (code) {
        SpeechRecognizer.ERROR_AUDIO -> "Error al capturar audio del micrófono."
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Permiso de micrófono requerido."
        SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
            "El dictado por voz requiere conexión de red o paquete offline de español."
        SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
            "No se escuchó un comando válido. Intenta hablar más claro."
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "El micrófono está ocupado, intenta de nuevo."
        SpeechRecognizer.ERROR_SERVER -> "Error del servicio de voz del sistema."
        else -> "No se pudo completar el reconocimiento de voz (código $code)."
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_RECORD_AUDIO && pendingStartAfterPermission) {
            pendingStartAfterPermission = false
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startSpeechRecognition(pendingLocale)
            } else {
                emitVoiceEvent("onListeningChanged", false)
                emitVoiceEvent(
                    "onError",
                    "Permiso de micrófono denegado. Habilítalo para usar comandos de voz."
                )
            }
        }
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_SPEECH_DIALOG) {
            isListening = false
            emitVoiceEvent("onListeningChanged", false)
            if (resultCode == Activity.RESULT_OK && data != null) {
                val results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                val recognized = results?.firstOrNull()?.trim().orEmpty()
                if (recognized.isNotEmpty()) {
                    emitVoiceEvent("onFinalResult", recognized)
                    return
                }
            }
            emitVoiceEvent("onError", "Dictado por voz cancelado o sin resultado.")
        }
    }

    private fun saveToDownloads(fileName: String, mimeType: String, bytes: ByteArray): String {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, mimeType)
                put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
            }
            val resolver = applicationContext.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw IllegalStateException("No se pudo crear el archivo en Descargas.")
            resolver.openOutputStream(uri)?.use { stream ->
                stream.write(bytes)
                stream.flush()
            } ?: throw IllegalStateException("No se pudo escribir el archivo en Descargas.")

            try {
                val viewIntent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, mimeType)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                if (viewIntent.resolveActivity(packageManager) != null) {
                    startActivity(viewIntent)
                }
            } catch (_: Exception) {
                // El archivo ya fue guardado en Descargas; si no hay visor instalado se notifica igual.
            }
            return "Descargas/$fileName"
        }

        val dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: filesDir
        if (!dir.exists()) {
            dir.mkdirs()
        }
        val outFile = File(dir, fileName)
        FileOutputStream(outFile).use { stream ->
            stream.write(bytes)
            stream.flush()
        }
        return outFile.absolutePath
    }

    override fun onDestroy() {
        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {
        }
        speechRecognizer = null
        super.onDestroy()
    }
}
