Pod::Spec.new do |s|
  s.name = 'FrameTraceShare'
  s.version = '0.1.0'
  s.summary = 'Private native video share inbox'
  s.description = 'FrameTrace host-side App Group import module'
  s.license = { :type => 'UNLICENSED' }
  s.author = 'FrameTrace'
  s.homepage = 'https://github.com/kenoyek/FrameTrace'
  s.source = { :git => 'https://github.com/kenoyek/FrameTrace.git' }
  s.platform = :ios, '16.4'
  s.swift_version = '5.9'
  s.static_framework = true
  s.dependency 'ExpoModulesCore'
  s.source_files = '*.swift'
end
