import 'package:flutter/material.dart';
import 'login_screen.dart'; // Login Screen import karna zaroori hai

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // Debug banner hatane ke liye
      title: 'Smart Attendance',
      theme: ThemeData(
        // Humne Purple theme rakha hai taaki UI se match kare
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      // App yahan se shuru hoga
      home: const LoginScreen(),
    );
  }
}