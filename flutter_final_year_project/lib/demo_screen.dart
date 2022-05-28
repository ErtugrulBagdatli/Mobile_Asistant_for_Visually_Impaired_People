import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_rating_bar/flutter_rating_bar.dart';
import 'package:flutter_final_year_project/backend.dart';

class Demo extends StatefulWidget {
  const Demo({Key? key}) : super(key: key);

  @override
  State<Demo> createState() => DemoState();
}

class DemoState extends State<Demo> {
  final Backend backend = Backend();
  static String _predictResult = "Your result will be here...";
  static String ip = "192.168.43.10"; // default ip
  static String port = "8080"; // default port
  static String requestId = "ID will be here..";
  String feedbackText = "";
  double feedbackRating = 3.0;
  final fieldText = TextEditingController();
  static bool isTurkish = false;
  static var languageText = 'Language: English';

  void toggleSwitch(bool value) {
    if (isTurkish == false) {
      setState(() {
        isTurkish = true;
        languageText = 'Language: Turkish';
      });
      if (kDebugMode) {
        print('Language: Turkish');
      }
    } else {
      setState(() {
        isTurkish = false;
        languageText = 'Language: English';
      });
      if (kDebugMode) {
        print('Language: English');
      }
    }
  }

  void clearText() {
    fieldText.clear();
  }

  static String getPredictedResult() {
    return _predictResult;
  }

  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          resizeToAvoidBottomInset: false,
          body: SingleChildScrollView(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const SizedBox(height: 10.0),
                const Text(
                  '--- This is a test version ---',
                  style: TextStyle(fontSize: 24, fontStyle: FontStyle.italic),
                ),

                /// Ip Data View and Edit Part
                const Divider(
                  height: 20,
                  thickness: 4,
                  color: Color(0x8383849E),
                ),
                Container(
                  margin: const EdgeInsets.all(8.0),
                  padding: const EdgeInsets.all(2.0),
                  decoration: const BoxDecoration(
                      color: Color(0xff440406),
                      borderRadius: BorderRadius.all(
                        Radius.circular(8.0),
                      )),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(30, 10, 30, 10),
                    child: Text(
                      ip + " : " + port,
                      style: const TextStyle(color: Colors.white, fontSize: 26),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 0),
                  child: TextField(
                    decoration: InputDecoration(
                      border: const OutlineInputBorder(),
                      labelText: 'Type to change Ip Address',
                      hintText: ip,
                    ),
                    onChanged: (text) {
                      setState(() {
                        ip = text;
                      });
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 0),
                  child: TextField(
                    decoration: InputDecoration(
                      border: const OutlineInputBorder(),
                      labelText: 'Type to change Port',
                      hintText: port,
                    ),
                    onChanged: (text) {
                      setState(() {
                        port = text;
                      });
                    },
                  ),
                ),

                /// Send Request Part
                const Divider(
                  height: 40,
                  thickness: 4,
                  color: Colors.grey,
                ),
                Text(
                  'Send Request From',
                  style: Theme.of(context).textTheme.headline6,
                ),
                const SizedBox(height: 8.0),
                Wrap(
                  children: <Widget>[
                    SizedBox.fromSize(
                      size: const Size(56, 56),
                      child: ClipOval(
                        child: Material(
                          color: Colors.purple,
                          child: InkWell(
                            onTap: () {
                              backend
                                  .getImageFromGallery(ip, port)
                                  .then((newResult) {
                                setState(() {
                                  _predictResult = newResult;
                                  if (backend.getId().length > 5) {
                                    requestId = backend.getId();
                                  }
                                });
                              });
                            },
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: const <Widget>[
                                Icon(
                                  Icons.add_photo_alternate_rounded,
                                  color: Colors.white,
                                  size: 30.0,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 30.0),
                    SizedBox.fromSize(
                      size: const Size(56, 56),
                      child: ClipOval(
                        child: Material(
                          color: Colors.deepPurpleAccent,
                          child: InkWell(
                            onTap: () {
                              backend
                                  .getImageFromCamera(ip, port)
                                  .then((newResult) {
                                setState(() {
                                  _predictResult = newResult;
                                  if (backend.getId().length > 5) {
                                    requestId = backend.getId();
                                  }
                                });
                              });
                            },
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: const <Widget>[
                                Icon(
                                  Icons.add_a_photo,
                                  color: Colors.white,
                                  size: 30.0,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8.0),

                /// Respond View Part
                const Divider(
                  height: 40,
                  thickness: 4,
                  color: Colors.grey,
                ),
                Column(
                  children: <Widget>[
                    Text(
                      'Response',
                      style: Theme.of(context).textTheme.headline6,
                    ),
                    Container(
                      margin: const EdgeInsets.all(10.0),
                      padding: const EdgeInsets.all(1.0),
                      decoration: const BoxDecoration(
                          color: Color(0xFF0441F8),
                          borderRadius: BorderRadius.all(
                            Radius.circular(8.0),
                          )),
                      child: Padding(
                        padding: const EdgeInsets.all(8),
                        child: Text(
                          _predictResult,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 16),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    )
                  ],
                ),

                /// Feed Form Part
                const Divider(
                  height: 40,
                  thickness: 4,
                  color: Colors.grey,
                ),
                Column(
                  children: <Widget>[
                    Text(
                      'Feedback',
                      style: Theme.of(context).textTheme.headline6,
                    ),
                    Container(
                      margin: const EdgeInsets.all(10.0),
                      padding: const EdgeInsets.all(1.0),
                      decoration: const BoxDecoration(
                          color: Color(0xFF0A4215),
                          borderRadius: BorderRadius.all(
                            Radius.circular(8.0),
                          )),
                      child: Padding(
                        padding: const EdgeInsets.all(8),
                        child: Text(
                          requestId,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 16),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    )
                  ],
                ),
                RatingBar(
                  initialRating: feedbackRating,
                  direction: Axis.horizontal,
                  allowHalfRating: true,
                  itemCount: 5,
                  ratingWidget: RatingWidget(
                    full: _image('assets/heart.png'),
                    half: _image('assets/heart_half.png'),
                    empty: _image('assets/heart_border.png'),
                  ),
                  itemPadding: const EdgeInsets.symmetric(horizontal: 4.0),
                  onRatingUpdate: (rating) {
                    setState(() {
                      feedbackRating = rating;
                    });
                  },
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(40, 10, 40, 10),
                  child: TextField(
                    controller: fieldText,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      labelText: 'Correct Respond',
                      hintText: 'Type the correct response',
                    ),
                    onChanged: (text) {
                      setState(() {
                        feedbackText = text;
                      });
                    },
                  ),
                ),
                RaisedButton(
                  color: const Color(0xffecb9a6),
                  onPressed: () {
                    backend
                        .feedbackPost(getIpAndPort(), Backend.id,
                            feedbackRating, feedbackText)
                        .then((value) {
                      setState(() {
                        requestId = value;
                        feedbackRating = 3.0;
                        fieldText.clear();
                      });
                    });
                    // Clear text box after send
                  },
                  child: const Text("Send Form"),
                ),

                /// Turkish Select
                const Divider(
                  height: 50,
                  thickness: 2,
                  color: Colors.grey,
                ),
                Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Transform.scale(
                      scale: 2,
                      child: Switch(
                        onChanged: toggleSwitch,
                        value: isTurkish,
                        activeColor: Colors.teal,
                        activeTrackColor: Colors.tealAccent.shade200,
                        inactiveThumbColor: Colors.redAccent,
                        inactiveTrackColor: Colors.orange.shade300,
                      )
                  ),
                  Text(
                    languageText,
                    style: TextStyle(fontSize: 20),
                  ),
                ]),

                /// Footer
                const Divider(
                  height: 50,
                  thickness: 2,
                  color: Colors.grey,
                ),
                const Text(
                  '2022 \u00a9 Repika | v7.3.3',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.grey,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 25.0),
              ],
            ),
          ),
        ));
  }

  static String getIpAndPort() {
    return ip + ":" + port;
  }
}

Widget _image(String asset) {
  return Image.asset(
    asset,
    height: 30.0,
    width: 30.0,
    color: Colors.amber,
  );
}
