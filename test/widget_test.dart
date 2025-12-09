import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vikramattendence/main.dart';

void main() {
  // Initialize the test environment
  TestWidgetsFlutterBinding.ensureInitialized();

  // This block sets up a "mock" or fake version of the GPS service before each test.
  setUp(() {
    // This is the internal channel that the geolocator plugin uses.
    const MethodChannel channel = MethodChannel('flutter.baseflow.com/geolocator');

    // Here, we define fake responses for the GPS service's methods.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(channel, (MethodCall methodCall) async {
      if (methodCall.method == 'isLocationServiceEnabled') {
        // Pretend that the GPS service is enabled.
        return true;
      }
      if (methodCall.method == 'checkPermission') {
        // Pretend that we already have permission to use the GPS.
        return 'granted';
      }
      if (methodCall.method == 'getCurrentPosition') {
        // Return a fake GPS position.
        return {
          'latitude': 51.507351,
          'longitude': -0.127758,
          'timestamp': DateTime.now().millisecondsSinceEpoch,
          'accuracy': 0.0,
          'altitude': 0.0,
          'altitudeAccuracy': 0.0,
          'heading': 0.0,
          'headingAccuracy': 0.0,
          'speed': 0.0,
          'speedAccuracy': 0.0,
          'isMocked': true,
        };
      }
      // For any other methods, do nothing.
      return null;
    });
  });

  // This block cleans up the mock after each test.
  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('flutter.baseflow.com/geolocator'),
      null,
    );
  });

  testWidgets('Attendance screen smoke test', (WidgetTester tester) async {
    // Build the AttendanceScreen widget.
    await tester.pumpWidget(MaterialApp(home: AttendanceScreen()));

    // Wait for all animations and async operations to complete.
    await tester.pumpAndSettle();

    // Check if the title is correct.
    expect(find.text('Attendance App'), findsOneWidget);

    // Check if the location status text has updated using the fake location.
    expect(find.byWidgetPredicate(
      (widget) => widget is Text && widget.data!.startsWith('Location Found!'),
    ), findsOneWidget);

    // Check if the punch in and punch out buttons are displayed.
    expect(find.text('PUNCH IN'), findsOneWidget);
    expect(find.text('PUNCH OUT'), findsOneWidget);
  });
}
