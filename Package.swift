// swift-tools-version: 5.7

import PackageDescription

let package = Package(
    name: "DesktopPetEngine",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "DesktopPetEngine", targets: ["DesktopPetEngine"])
    ],
    targets: [
        .executableTarget(
            name: "DesktopPetEngine",
            path: "Sources/DesktopPetEngine",
            resources: [
                .copy("Assets")
            ]
        )
    ]
)
