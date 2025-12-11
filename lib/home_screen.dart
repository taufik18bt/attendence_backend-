import 'package:url_launcher/url_launcher.dart'; // 1. Import
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;

// ⚠️ APNA RENDER URL YAHAN HAI
const String baseUrl = "https://attendence-backend-2.onrender.com";

class HomeScreen extends StatefulWidget {
  final Map<String, dynamic> user;
  const HomeScreen({super.key, required this.user});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _timeString = "";
  String _dateString = "";
  bool _isLoading = false;
  String _status = "Tap to Punch"; 

  @override
  void initState() {
    _timeString = _formatTime(DateTime.now());
    _dateString = _formatDate(DateTime.now());
    Timer.periodic(const Duration(seconds: 1), (Timer t) => _getTime());
    super.initState();
  }

  void _getTime() {
    final DateTime now = DateTime.now();
    if (mounted) {
      setState(() {
        _timeString = _formatTime(now);
        _dateString = _formatDate(now);
      });
    }
  }

  String _formatTime(DateTime dateTime) {
    return DateFormat('hh:mm:ss a').format(dateTime);
  }

  String _formatDate(DateTime dateTime) {
    return DateFormat('EEEE, d MMMM y').format(dateTime);
  }

  // --- API PUNCH FUNCTION ---
  Future<void> _handlePunch(String type) async {
    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/punch"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "user_id": widget.user['id'], 
          "punch_type": type,           
          "latitude": 24.6721,          
          "longitude": 81.8893,
          "device_id": "MOBILE_APP"
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        setState(() {
          _status = type == "IN" ? "🟢 Punched IN" : "🔴 Punched OUT";
        });
        _showMsg("Success! Punch Accepted.", Colors.green);
      } else {
        _showMsg(data['detail'] ?? "Failed to mark attendance", Colors.red);
      }
    } catch (e) {
      _showMsg("Error: Internet check karein", Colors.red);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showMsg(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: color,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF4A00E0), Color(0xFF8E2DE2)], 
          ),
        ),
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // --- HEADER ---
              Padding(
                padding: const EdgeInsets.all(24.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Welcome,",
                          style: GoogleFonts.poppins(color: Colors.white70, fontSize: 16),
                        ),
                        Text(
                          widget.user['full_name'] ?? "User",
                          style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const CircleAvatar(
                      radius: 25,
                      backgroundColor: Colors.white24,
                      child: Icon(Icons.person, color: Colors.white),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 10),

              // --- CLOCK CARD ---
              Center(
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 24),
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: Colors.white30),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _timeString,
                        style: GoogleFonts.robotoMono(
                          color: Colors.white,
                          fontSize: 40,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _dateString,
                        style: GoogleFonts.poppins(color: Colors.white70, fontSize: 14),
                      ),
                      const Divider(color: Colors.white24, height: 30),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.location_on, color: Colors.orangeAccent, size: 18),
                          const SizedBox(width: 8),
                          Text(
                            "Head Office", 
                            style: GoogleFonts.poppins(color: Colors.white),
                          ),
                        ],
                      )
                    ],
                  ),
                ),
              ),

              const Spacer(),

              // --- BOTTOM SHEET (Buttons) ---
              Container(
                padding: const EdgeInsets.all(30),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(40),
                    topRight: Radius.circular(40),
                  ),
                ),
                child: Column(
                  children: [
                    Text(
                      "Current Status",
                      style: GoogleFonts.poppins(color: Colors.grey),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      _status,
                      style: GoogleFonts.poppins(
                        color: Colors.black87,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 30),
                    
                    _isLoading 
                    ? const CircularProgressIndicator()
                    : Row(
                      children: [
                        Expanded(
                          child: _buildButton(
                            "PUNCH IN", 
                            Colors.green, 
                            Icons.login, 
                            () => _handlePunch("IN")
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: _buildButton(
                            "PUNCH OUT", 
                            Colors.redAccent, 
                            Icons.logout, 
                            () => _handlePunch("OUT")
                          ),
                        ),
                      ],
                    ),

                    // ✅ NEW: ADMIN LOGIN BUTTON ADDED HERE
                    const SizedBox(height: 20),
                    TextButton.icon(
                      onPressed: () {
                        _showAdminPasswordDialog(context);
                      },
                      icon: const Icon(Icons.admin_panel_settings, color: Colors.blueGrey),
                      label: const Text(
                        "Admin Login",
                        style: TextStyle(color: Colors.blueGrey, fontSize: 16, decoration: TextDecoration.underline),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // --- BUTTON DESIGN WIDGET ---
  Widget _buildButton(String title, Color color, IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 60,
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: color, width: 2),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 10),
            Text(
              title,
              style: GoogleFonts.poppins(
                color: color,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ✅ NEW: PASSWORD DIALOG FUNCTION ADDED HERE (At the bottom)
  void _showAdminPasswordDialog(BuildContext context) {
    final TextEditingController passwordController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("🔐 Admin Access"),
          content: TextField(
            controller: passwordController,
            obscureText: true, 
            decoration: const InputDecoration(
              hintText: "Admin Password daliye",
              border: OutlineInputBorder(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: () async {
                // 🔐 PASSWORD YAHAN SET HAI: '12345'
                if (passwordController.text == "12345") {
                  Navigator.pop(context); 
                  
                  // Apni Admin Site ka URL yahan dalein
                  final Uri url = Uri.parse("https://attendance-admin-9ny9.onrender.com");
                  
                  if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Could not launch Admin Panel")),
                    );
                  }
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("❌ Galat Password!"),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              child: const Text("Login"),
            ),
          ],
        );
      },
    );
  }
}