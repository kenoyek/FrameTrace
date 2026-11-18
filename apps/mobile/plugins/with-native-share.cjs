const fs = require('node:fs');
const path = require('node:path');
const { withAndroidManifest, withEntitlementsPlist, withInfoPlist, withXcodeProject } = require('expo/config-plugins');
const plist = require('@expo/plist').default;
const TARGET = 'FrameTraceShare';

function withNativeShare(config, options = {}) {
  const bundle = config.ios?.bundleIdentifier;
  if (!bundle) throw new Error('FrameTrace sharing requires an iOS bundle identifier.');
  const group = options.appGroup ?? `group.${bundle}`;
  if (!/^group\.[A-Za-z0-9.-]+$/.test(group)) throw new Error('Invalid App Group identifier.');
  const extensionBundle = `${bundle}.share`;
  const extensions = config.extra?.eas?.build?.experimental?.ios?.appExtensions ?? [];
  config.extra = { ...config.extra, eas: { ...config.extra?.eas, build: {
    ...config.extra?.eas?.build, experimental: { ...config.extra?.eas?.build?.experimental, ios: {
      ...config.extra?.eas?.build?.experimental?.ios,
      appExtensions: [...extensions.filter(entry => entry.targetName !== TARGET), {
        targetName: TARGET, bundleIdentifier: extensionBundle,
        entitlements: { 'com.apple.security.application-groups': [group] },
      }],
    } },
  } } };
  config = withAndroidManifest(config, mod => {
    const application = mod.modResults.manifest.application?.[0];
    const activity = application?.activity?.find(item => item.$['android:name'] === '.MainActivity');
    if (!activity) throw new Error('MainActivity missing; native sharing was not configured.');
    activity.$['android:launchMode'] = 'singleTask';
    const filters = activity['intent-filter'] ?? [];
    const name = 'Identify with FrameTrace';
    activity['intent-filter'] = [...filters.filter(item => item.$?.['android:label'] !== name), {
      $: { 'android:label': name }, action: [{ $: { 'android:name': 'android.intent.action.SEND' } }],
      category: [{ $: { 'android:name': 'android.intent.category.DEFAULT' } }],
      data: [{ $: { 'android:mimeType': 'video/*' } }, { $: { 'android:mimeType': 'text/plain' } }],
    }];
    return mod;
  });
  config = withEntitlementsPlist(config, mod => {
    const existing = mod.modResults['com.apple.security.application-groups'] ?? [];
    mod.modResults['com.apple.security.application-groups'] = [...new Set([...existing, group])];
    return mod;
  });
  config = withInfoPlist(config, mod => { mod.modResults.FrameTraceAppGroup = group; return mod; });
  return withXcodeProject(config, mod => {
    const project = mod.modResults;
    const dir = path.join(mod.modRequest.platformProjectRoot, TARGET);
    fs.mkdirSync(dir, { recursive: true });
    fs.copyFileSync(path.join(__dirname, 'native-share/ShareViewController.swift'), path.join(dir, 'ShareViewController.swift'));
    fs.writeFileSync(path.join(dir, `${TARGET}.entitlements`), plist.build({ 'com.apple.security.application-groups': [group] }));
    fs.writeFileSync(path.join(dir, 'Info.plist'), plist.build({
      CFBundleDisplayName: 'FrameTrace', CFBundleExecutable: '$(EXECUTABLE_NAME)',
      CFBundleIdentifier: '$(PRODUCT_BUNDLE_IDENTIFIER)', CFBundleInfoDictionaryVersion: '6.0',
      CFBundleName: '$(PRODUCT_NAME)', CFBundlePackageType: 'XPC!',
      CFBundleShortVersionString: config.version ?? '0.1.0', CFBundleVersion: config.ios?.buildNumber ?? '1',
      FrameTraceAppGroup: group,
      NSExtension: { NSExtensionPointIdentifier: 'com.apple.share-services',
        NSExtensionPrincipalClass: '$(PRODUCT_MODULE_NAME).ShareViewController',
        NSExtensionAttributes: { NSExtensionActivationRule: {
          NSExtensionActivationSupportsMovieWithMaxCount: 1,
          NSExtensionActivationSupportsWebURLWithMaxCount: 1,
          NSExtensionActivationSupportsText: true,
        } },
      },
    }));
    const groups = project.hash.project.objects.PBXGroup;
    const existingGroup = Object.entries(groups).find(([, value]) => typeof value === 'object' && value.name?.replaceAll('"', '') === TARGET);
    if (!existingGroup) {
      const group = project.addPbxGroup([`${TARGET}/ShareViewController.swift`, `${TARGET}/Info.plist`, `${TARGET}/${TARGET}.entitlements`], TARGET);
      project.addToPbxGroup(group.uuid, project.getFirstProject().firstProject.mainGroup);
    }
    // Fresh Expo projects have no dependency/proxy sections; node-xcode silently skips
    // addTargetDependency unless both sections already exist.
    project.hash.project.objects.PBXTargetDependency ??= {};
    project.hash.project.objects.PBXContainerItemProxy ??= {};
    const existing = Object.entries(project.pbxNativeTargetSection()).find(([, value]) => typeof value === 'object' && value.name?.replaceAll('"', '') === TARGET);
    const target = existing ? { uuid: existing[0], pbxNativeTarget: existing[1] } : project.addTarget(TARGET, 'app_extension', TARGET, extensionBundle);
    if (!existing) {
      project.addBuildPhase([`${TARGET}/ShareViewController.swift`], 'PBXSourcesBuildPhase', 'Sources', target.uuid);
      project.addBuildPhase([], 'PBXFrameworksBuildPhase', 'Frameworks', target.uuid);
    }
    const host = project.getFirstTarget();
    const dependencies = project.hash.project.objects.PBXTargetDependency;
    if (!host.firstTarget.dependencies.some(dep => dependencies[dep.value]?.target === target.uuid)) {
      project.addTargetDependency(host.uuid, [target.uuid]);
    }
    const configurations = project.pbxXCBuildConfigurationSection();
    const list = project.pbxXCConfigurationList()[target.pbxNativeTarget.buildConfigurationList];
    for (const item of list.buildConfigurations) {
      const settings = configurations[item.value].buildSettings;
      Object.assign(settings, {
        INFOPLIST_FILE: `"${TARGET}/Info.plist"`, CODE_SIGN_ENTITLEMENTS: `"${TARGET}/${TARGET}.entitlements"`,
        SWIFT_VERSION: '5.9', IPHONEOS_DEPLOYMENT_TARGET: '16.4',
        APPLICATION_EXTENSION_API_ONLY: 'YES', TARGETED_DEVICE_FAMILY: '"1,2"',
        GENERATE_INFOPLIST_FILE: 'NO', CURRENT_PROJECT_VERSION: config.ios?.buildNumber ?? '1',
        MARKETING_VERSION: config.version ?? '0.1.0', CODE_SIGN_STYLE: 'Automatic',
      });
      if (config.ios?.appleTeamId) settings.DEVELOPMENT_TEAM = config.ios.appleTeamId;
    }
    project.addTargetAttribute('SystemCapabilities', { 'com.apple.ApplicationGroups.iOS': { enabled: 1 } }, target.uuid);
    return mod;
  });
}
module.exports = withNativeShare;
