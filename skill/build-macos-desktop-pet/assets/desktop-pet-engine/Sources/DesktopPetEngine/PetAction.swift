import Foundation

enum PetAction: String, CaseIterable {
    case idle
    case walk
    case dance
    case playBall
    case eat
    case drink
    case yawn
    case frustrated
    case crying
    case shy
    case happy
    case rowing
    case meditation

    var chineseTitle: String {
        switch self {
        case .idle: return "待机"
        case .walk: return "走路"
        case .dance: return "跳舞"
        case .playBall: return "玩球"
        case .eat: return "吃饭"
        case .drink: return "喝水"
        case .yawn: return "打哈欠"
        case .frustrated: return "抓狂"
        case .crying: return "哭泣"
        case .shy: return "害羞"
        case .happy: return "开心"
        case .rowing: return "划船"
        case .meditation: return "冥想"
        }
    }

    static let autonomousOrder: [PetAction] = [
        .walk, .dance, .playBall, .eat, .drink, .yawn
    ]

    static let menuActions: [PetAction] = autonomousOrder + [
        .frustrated, .crying, .shy, .happy, .rowing, .meditation
    ]
}

enum PetSize: String, CaseIterable {
    case small
    case medium
    case large

    var chineseTitle: String {
        switch self {
        case .small: return "小"
        case .medium: return "中"
        case .large: return "大"
        }
    }

    var sideLength: CGFloat {
        switch self {
        case .small: return 220
        case .medium: return 300
        case .large: return 420
        }
    }
}

enum CursorDirection: String {
    case center
    case right
    case upRight
    case up
    case upLeft
    case left
    case downLeft
    case down
    case downRight

    static func from(deltaX: CGFloat, deltaY: CGFloat) -> CursorDirection {
        guard abs(deltaX) + abs(deltaY) > 1 else { return .center }
        let angle = atan2(deltaY, deltaX) * 180 / .pi

        switch angle {
        case -22.5..<22.5: return .right
        case 22.5..<67.5: return .upRight
        case 67.5..<112.5: return .up
        case 112.5..<157.5: return .upLeft
        case 157.5...180, -180 ..< -157.5: return .left
        case -157.5 ..< -112.5: return .downLeft
        case -112.5 ..< -67.5: return .down
        default: return .downRight
        }
    }
}
