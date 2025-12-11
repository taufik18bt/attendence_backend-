import 'package:flutter/material.dart';
import 'login_screen.dart'; // <--- Zaroori


class ApiService {
  // ❌ PURANA HATAO:

  // ✅ NAYA LAGAO (Apna Render Web Service URL):
  static const String baseUrl = "https://attendence-backend-2.onrender.com";
  // (Last mein slash '/' mat lagana)
}
void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Vikram Attendance',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const LoginScreen(), // <--- Ye LoginScreen khol raha hai
    );
  }
}