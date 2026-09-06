import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
    kotlin("jvm") version "2.0.21"
    kotlin("plugin.compose") version "2.0.21"
    id("org.jetbrains.compose") version "1.7.1"
    kotlin("plugin.serialization") version "2.0.21"
}

group = "com.gsgc"
version = "2.0.0"

repositories {
    google()
    mavenCentral()
    maven("https://maven.pkg.jetbrains.space/public/p/compose/dev")
}

dependencies {
    implementation(compose.desktop.currentOs)
    implementation(compose.material3)
    implementation(compose.materialIconsExtended)

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    // Document processing
    implementation("org.apache.poi:poi-ooxml:5.3.0")
    implementation("org.apache.pdfbox:pdfbox:3.0.3")

    // Archive processing
    implementation("org.apache.commons:commons-compress:1.27.1")

    // Windows registry & shortcut (autostart, theme accent)
    implementation("net.java.dev.jna:jna:5.14.0")
    implementation("net.java.dev.jna:jna-platform:5.14.0")

    // Image format plugins (webp, tiff)
    implementation("org.sejda.imageio:webp-imageio:0.1.6")
    implementation("com.twelvemonkeys.imageio:imageio-tiff:3.10.1")
    implementation("com.twelvemonkeys.imageio:imageio-bmp:3.10.1")

    testImplementation(kotlin("test"))
}

compose.desktop {
    application {
        mainClass = "com.gsgc.converter.MainKt"
        // OpenGL 渲染后端 + 高 DPI 感知，避免 Windows 缩放（125%/150%）下文字模糊
        jvmArgs += listOf(
            "-Dskiko.rendering.api=opengl",
            "-Dorg.jetbrains.skiko.rendering.api=opengl",
            "-Dsun.java2d.dpiaware=true",
            "-Dsun.java2d.uiScale.enabled=true"
        )
        nativeDistributions {
            targetFormats(TargetFormat.Msi, TargetFormat.Exe)
            packageName = "FormatConverter"
            packageVersion = "2.0.0"
            description = "格式转换工具 - 音视频/图片/文档/压缩包格式转换"
            vendor = "GSGC"
            windows {
                menu = true
                perUserInstall = true
                iconFile.set(project.file("logo.ico"))
            }
            linux {
                iconFile.set(project.file("logo.ico"))
            }
            macOS {
                iconFile.set(project.file("logo.ico"))
            }
        }
    }
}

kotlin {
    jvmToolchain(17)
}

tasks.test {
    useJUnitPlatform()
}

// 导出运行时依赖 jar 到 build/exportLibs，供免安装打包脚本使用
tasks.register<Copy>("exportRuntimeLibs") {
    from(configurations.runtimeClasspath)
    into(layout.buildDirectory.dir("exportLibs"))
}
