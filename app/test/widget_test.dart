import 'package:flutter_test/flutter_test.dart';

import 'package:my_news/main.dart';

void main() {
  testWidgets('App builds and displays My News', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('My News'), findsWidgets);
  });
}
