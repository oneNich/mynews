class Config {
  static const String defaultApiUrl = 'https://mynews-fdgy.onrender.com';

  static String get apiUrl {
    // In a real app, this would read from --dart-define=API_URL
    // For now, use the default URL
    const String apiUrlFromDefine = String.fromEnvironment(
      'API_URL',
      defaultValue: defaultApiUrl,
    );
    return apiUrlFromDefine;
  }
}
