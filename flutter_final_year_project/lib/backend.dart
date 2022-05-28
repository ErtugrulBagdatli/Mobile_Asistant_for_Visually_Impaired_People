import 'dart:io';
import 'dart:typed_data';

import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_final_year_project/demo_screen.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:translator/translator.dart';

class Backend {
  static String id = "";
  static String sendId = "";
  static final translator = GoogleTranslator();

  /// (POST) to "/feed/image" and TTS
  Future<String> uploadImage(
      String pathImage, Uint8List bytes, String ipAndPort) async {
    // Text-to-speech initialize.
    final FlutterTts tts = FlutterTts();

    // TODO: token specialization
    //request.headers['Authorization'] = "Client-ID " + "f7........";

    // Creating post request var.
    var request = http.MultipartRequest(
        "POST", Uri.parse("http://" + ipAndPort + "/feed/image"));
    request.fields['file'] = "file";

    // Parsing image path.
    String imageFullName = pathImage.split('/').last;
    String imgExt = imageFullName.split('.').last;

    // Creating multipart request body.
    var picture = http.MultipartFile.fromBytes(
      'file',
      bytes,
      filename: imgExt,
      contentType: MediaType('image', imgExt),
    );
    request.files.add(picture);

    // Sending request and getting response.
    var response = await request.send();
    var responseData = await response.stream.toBytes();
    var jsonResponse = String.fromCharCodes(responseData);
    final parsedJson = jsonDecode(jsonResponse);

    if (kDebugMode) {
      print('${parsedJson.runtimeType} : $parsedJson');
    }

    // String modify
    int index = parsedJson.toString().indexOf(',');
    id = parsedJson.toString().substring(5, index);
    String result = parsedJson
        .toString()
        .substring(index + 10, parsedJson.toString().length - 1);

    // Translation
    var translation = await translator.translate(result, from: 'en', to: 'tr');

    // Speaking result to the user
    if(DemoState.isTurkish) {
      tts.setLanguage('tr');
      tts.setSpeechRate(0.5);
      tts.speak(translation.toString());
      return translation.toString();
    }
    else {
      tts.setLanguage('en');
      tts.setSpeechRate(0.5);
      tts.speak(result);
      return result;
    }
  }

  /// (POST) to "/feed"
  Future<String> feedbackPost(
      String ipAndPort, String id, double score, String feedbackText) async {
    String answer = "ID will be here..";
    // Validation
    if (id.length > 5) {

      if(sendId == id) {
        return "You cannot re-send form with same ID!";
      }
      if (feedbackText.isEmpty) {
        feedbackText = "NaN";
      }

      if (kDebugMode) {
        print("--------feedback--------");
        print("-> " + ipAndPort);
        print("-> " + id);
        print("-> " + score.toString());
        print("-> " + feedbackText);
      }

      // Request preparation
      Map<String, String> queryParameters = {
        'caption_id': id,
        'score': score.toString(),
        'feedback': feedbackText,
      };
      final uri = Uri.http(ipAndPort, '/feed', queryParameters);
      var request = http.MultipartRequest("POST", uri);

      // Sending request and getting response.
      var response = await request.send();
      var responseData = await response.stream.toBytes();
      var jsonResponse = String.fromCharCodes(responseData);
      answer = jsonDecode(jsonResponse).toString();

      if (kDebugMode) {
        print(answer);
      }
    }
    sendId = id;
    return answer + "!";
  }

  /// Get from Gallery
  Future<String> getImageFromGallery(String ip, String port) async {
    ImagePicker _imagePicker = ImagePicker();
    var image = await _imagePicker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      String ext = image.path;
      final bytes = await image.readAsBytes();

      String ipAndPort = ip + ":" + port;

      return uploadImage(ext, bytes, ipAndPort);
    }
    return "Your result will be here...";
  }

  /// Get from Camera
  Future<String> getImageFromCamera(String ip, String port) async {
    ImagePicker _imagePicker = ImagePicker();
    var image = await _imagePicker.pickImage(source: ImageSource.camera);
    if (image != null) {
      String ext = image.path;
      final bytes = await image.readAsBytes();

      String ipAndPort = ip + ":" + port;

      return uploadImage(ext, bytes, ipAndPort);
    }
    return "Your result will be here...";
  }

  /// Get from Gallery
  Future<String> getRespondWithImage(String ipAndPort, File image) async {
    if (image != null) {
      String ext = image.path;
      final bytes = await image.readAsBytes();

      return uploadImage(ext, bytes, ipAndPort);
    }
    return "Your result will be here...";
  }

  String getId() {
    return id;
  }
}
