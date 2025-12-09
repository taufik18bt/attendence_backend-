import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// --- CONFIGURATION ---



// Naya (Ye paste karein):
final String baseUrl = "https://attendence-backend-1-66d0.onrender.com";

void main() {
  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    home: LoginScreen(), // Sabse pehle Login Screen khulegi
  ));
}

// ---------------- LOGIN SCREEN ----------------
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _mobileController = TextEditingController();
  bool isLoading = false;

  Future<void> _login() async {
    String mobile = _mobileController.text.trim();
    if (mobile.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Enter Mobile Number")));
      return;
    }

    setState(() => isLoading = true);

    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/login"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"mobile_number": mobile}),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        // Success! User details nikalo
        var user = data['user'];
        
        // Agli Screen par jao (User ID aur Name lekar)
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => AttendanceScreen(
              userId: user['id'],
              userName: user['full_name'],
            ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(data['detail'] ?? "Login Failed"), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Connection Error: $e"), backgroundColor: Colors.red));
    }

    setState(() => isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Employee Login")),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.lock_person, size: 80, color: Colors.blue),
            SizedBox(height: 20),
            TextField(
              controller: _mobileController,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: "Mobile Number",
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.phone),
              ),
            ),
            SizedBox(height: 20),
            isLoading
                ? CircularProgressIndicator()
                : SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _login,
                      style: ElevatedButton.styleFrom(padding: EdgeInsets.all(15)),
                      child: Text("LOGIN", style: TextStyle(fontSize: 18)),
                    ),
                  ),
          ],
        ),
      ),
    );
  }
}

// ---------------- ATTENDANCE SCREEN ----------------
class AttendanceScreen extends StatefulWidget {
  final int userId;
  final String userName;

  AttendanceScreen({required this.userId, required this.userName});

  @override
  _AttendanceScreenState createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  String status = "Waiting for Location...";
  bool isLoading = false;
  Position? currentPosition;

  @override
  void initState() {
    super.initState();
    _determinePosition();
  }

  Future<void> _determinePosition() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      setState(() => status = "Please enable GPS.");
      return;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }

    setState(() => status = "Fetching Location...");
    Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);

    setState(() {
      currentPosition = position;
      status = "Location Found!\nLat: ${position.latitude.toStringAsFixed(4)}\nLng: ${position.longitude.toStringAsFixed(4)}";
    });
  }

  Future<void> _punch(String type) async {
    if (currentPosition == null) {
      _determinePosition();
      return;
    }

    setState(() => isLoading = true);

    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/punch"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "user_id": widget.userId, // <--- Ab ye Login wale user ki ID lega
          "punch_type": type,
          "latitude": currentPosition!.latitude,
          "longitude": currentPosition!.longitude,
          "device_id": "MOBILE_APP"
        }),
      );

      final respData = jsonDecode(response.body);

      if (response.statusCode == 200) {
        _showMessage("Success: ${respData['message']}", Colors.green);
      } else {
        _showMessage("Failed: ${respData['detail']}", Colors.red);
      }
    } catch (e) {
      _showMessage("Connection Error", Colors.red);
    }

    setState(() => isLoading = false);
  }

  void _showMessage(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: color));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Welcome, ${widget.userName}")), // User ka naam dikhayega
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.location_on, size: 60, color: Colors.blueAccent),
              SizedBox(height: 20),
              Text(status, textAlign: TextAlign.center, style: TextStyle(fontSize: 16)),
              SizedBox(height: 40),
              isLoading
                  ? CircularProgressIndicator()
                  : Column(
                      children: [
                        SizedBox(width: double.infinity, child: ElevatedButton(
                          onPressed: () => _punch("IN"),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.green, padding: EdgeInsets.all(15)),
                          child: Text("PUNCH IN", style: TextStyle(color: Colors.white, fontSize: 18)),
                        )),
                        SizedBox(height: 20),
                        SizedBox(width: double.infinity, child: ElevatedButton(
                          onPressed: () => _punch("OUT"),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.red, padding: EdgeInsets.all(15)),
                          child: Text("PUNCH OUT", style: TextStyle(color: Colors.white, fontSize: 18)),
                        )),
                      ],
                    )
            ],
          ),
        ),
      ),
    );
  }
}