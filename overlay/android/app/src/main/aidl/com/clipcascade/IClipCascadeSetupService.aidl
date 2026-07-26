package com.clipcascade;

interface IClipCascadeSetupService {
    String applySetup(String packageName);
    String inspectSetup(String packageName);
    void destroy();
}
