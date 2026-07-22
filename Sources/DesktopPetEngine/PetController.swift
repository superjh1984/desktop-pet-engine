import AppKit

final class PetController: NSObject {
    private enum PlaybackMode {
        case idle
        case manual(PetAction)
        case autonomous(Int)

        var isIdle: Bool {
            if case .idle = self { return true }
            return false
        }
    }

    private let window: PetWindow
    private let view: PetView
    private let assets: AssetCatalog

    private var mode: PlaybackMode = .idle
    private var playbackTimer: Timer?
    private var mouseTimer: Timer?
    private var inactivityTimer: Timer?
    private var currentClip: AnimationClip?
    private var frameIndex = 0
    private var wasHoveringPet = false
    private var currentIdleDirection: CursorDirection = .center
    private(set) var currentSize: PetSize = .medium

    init(window: PetWindow, view: PetView, assets: AssetCatalog) {
        self.window = window
        self.view = view
        self.assets = assets
        super.init()
    }

    func start() {
        enterIdle(resetCountdown: true)
        mouseTimer = Timer.scheduledTimer(
            timeInterval: 1.0 / 30.0,
            target: self,
            selector: #selector(updateMouseState),
            userInfo: nil,
            repeats: true
        )
        mouseTimer?.tolerance = 0.01
    }

    func handleLeftClick(clickCount: Int) {
        if mode.isIdle {
            if clickCount >= 2 {
                startAutonomousMode()
            } else {
                userDidInteract()
            }
        } else {
            enterIdle(resetCountdown: true)
        }
    }

    func userDidInteract() {
        if mode.isIdle {
            scheduleInactivityCountdown()
        }
    }

    func showPet() {
        ensureWindowIsOnScreen()
        window.orderFrontRegardless()
        enterIdle(resetCountdown: true)
    }

    func hidePet() {
        playbackTimer?.invalidate()
        inactivityTimer?.invalidate()
        window.orderOut(nil)
    }

    func makeContextMenu() -> NSMenu {
        let menu = NSMenu(title: "桌宠引擎")
        menu.autoenablesItems = false

        for action in PetAction.menuActions {
            let item = NSMenuItem(
                title: action.chineseTitle,
                action: #selector(selectManualAction(_:)),
                keyEquivalent: ""
            )
            item.target = self
            item.representedObject = action.rawValue
            menu.addItem(item)
        }

        menu.addItem(.separator())
        let randomItem = NSMenuItem(title: "随机动作", action: #selector(selectRandomAction), keyEquivalent: "")
        randomItem.target = self
        menu.addItem(randomItem)

        let idleItem = NSMenuItem(title: "待机", action: #selector(selectIdle), keyEquivalent: "")
        idleItem.target = self
        idleItem.state = mode.isIdle ? .on : .off
        menu.addItem(idleItem)

        let sizeItem = NSMenuItem(title: "调整大小", action: nil, keyEquivalent: "")
        let sizeMenu = NSMenu(title: "调整大小")
        for petSize in PetSize.allCases {
            let item = NSMenuItem(
                title: petSize.chineseTitle,
                action: #selector(selectSize(_:)),
                keyEquivalent: ""
            )
            item.target = self
            item.representedObject = petSize.rawValue
            item.state = currentSize == petSize ? .on : .off
            sizeMenu.addItem(item)
        }
        menu.setSubmenu(sizeMenu, for: sizeItem)
        menu.addItem(sizeItem)

        menu.addItem(.separator())
        let aboutItem = NSMenuItem(title: "关于", action: #selector(selectAbout), keyEquivalent: "")
        aboutItem.target = self
        menu.addItem(aboutItem)

        menu.addItem(.separator())
        let hideItem = NSMenuItem(title: "隐藏", action: #selector(selectHide), keyEquivalent: "")
        hideItem.target = self
        menu.addItem(hideItem)

        let quitItem = NSMenuItem(title: "退出", action: #selector(selectQuit), keyEquivalent: "")
        quitItem.target = self
        menu.addItem(quitItem)
        return menu
    }

    @objc private func selectManualAction(_ sender: NSMenuItem) {
        guard let rawValue = sender.representedObject as? String,
              let action = PetAction(rawValue: rawValue) else { return }
        playManualAction(action)
    }

    @objc private func selectRandomAction() {
        let available = PetAction.menuActions.filter { assets.hasClip(for: $0) }
        guard let action = available.randomElement() else {
            view.showMessage("动作素材待补")
            enterIdle(resetCountdown: true)
            return
        }
        playManualAction(action)
    }

    @objc private func selectIdle() {
        enterIdle(resetCountdown: true)
    }

    @objc private func selectSize(_ sender: NSMenuItem) {
        guard let rawValue = sender.representedObject as? String,
              let size = PetSize(rawValue: rawValue) else { return }
        resize(to: size)
    }

    @objc private func selectHide() {
        hidePet()
    }

    @objc private func selectAbout() {
        window.ignoresMouseEvents = false
        NSApp.activate(ignoringOtherApps: true)

        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "未知"
        let alert = NSAlert()
        alert.alertStyle = .informational
        alert.messageText = "关于桌宠引擎"
        alert.informativeText = """
        版本号: \(version)
        开源桌宠引擎示例
        代码与示例素材采用 Apache-2.0 许可证
        """
        alert.icon = NSImage(named: NSImage.applicationIconName)
        alert.addButton(withTitle: "好")
        alert.runModal()
    }

    @objc private func selectQuit() {
        NSApp.terminate(nil)
    }

    private func playManualAction(_ action: PetAction) {
        guard let clip = assets.clip(for: action) else {
            view.showMessage("“\(action.chineseTitle)”素材待补")
            enterIdle(resetCountdown: true)
            return
        }
        mode = .manual(action)
        startPlayback(clip)
    }

    private func startAutonomousMode() {
        inactivityTimer?.invalidate()
        playAutonomousAction(at: 0)
    }

    private func playAutonomousAction(at requestedIndex: Int) {
        var index = requestedIndex
        while index < PetAction.autonomousOrder.count {
            let action = PetAction.autonomousOrder[index]
            if let clip = assets.clip(for: action) {
                mode = .autonomous(index)
                startPlayback(clip)
                return
            }
            index += 1
        }
        enterIdle(resetCountdown: true)
    }

    private func startPlayback(_ clip: AnimationClip) {
        playbackTimer?.invalidate()
        inactivityTimer?.invalidate()
        currentClip = clip
        frameIndex = 0
        displayFrame(clip.image(at: 0))

        let timer = Timer.scheduledTimer(
            timeInterval: 1.0 / clip.fps,
            target: self,
            selector: #selector(advancePlaybackFrame),
            userInfo: nil,
            repeats: true
        )
        timer.tolerance = min(0.01, 0.25 / clip.fps)
        playbackTimer = timer
    }

    @objc private func advancePlaybackFrame() {
        guard let clip = currentClip else { return }
        frameIndex += 1
        if frameIndex < clip.frameCount {
            displayFrame(clip.image(at: frameIndex))
            return
        }

        playbackTimer?.invalidate()
        playbackTimer = nil
        switch mode {
        case .manual:
            enterIdle(resetCountdown: true)
        case .autonomous(let index):
            playAutonomousAction(at: index + 1)
        case .idle:
            enterIdle(resetCountdown: true)
        }
    }

    private func enterIdle(resetCountdown: Bool) {
        playbackTimer?.invalidate()
        playbackTimer = nil
        currentClip = assets.clip(for: .idle)
        frameIndex = 0
        mode = .idle
        currentIdleDirection = .center

        if let idleClip = currentClip {
            displayFrame(idleClip.image(for: .center))
        }
        if resetCountdown {
            scheduleInactivityCountdown()
        }
    }

    private func scheduleInactivityCountdown() {
        inactivityTimer?.invalidate()
        let delay = TimeInterval.random(in: 45...120)
        inactivityTimer = Timer.scheduledTimer(
            timeInterval: delay,
            target: self,
            selector: #selector(inactivityCountdownFinished),
            userInfo: nil,
            repeats: false
        )
        inactivityTimer?.tolerance = 1
    }

    @objc private func inactivityCountdownFinished() {
        guard mode.isIdle, window.isVisible else { return }
        startAutonomousMode()
    }

    @objc private func updateMouseState() {
        guard window.isVisible else { return }
        let screenPoint = NSEvent.mouseLocation
        let windowPoint = NSPoint(
            x: screenPoint.x - window.frame.minX,
            y: screenPoint.y - window.frame.minY
        )
        let isOverOpaquePixel = view.containsOpaquePixel(atWindowPoint: windowPoint)

        let mouseButtonIsDown = NSEvent.pressedMouseButtons != 0
        window.ignoresMouseEvents = !isOverOpaquePixel && !mouseButtonIsDown

        if mode.isIdle, let idleClip = assets.clip(for: .idle) {
            let dx = screenPoint.x - window.frame.midX
            let dy = screenPoint.y - window.frame.midY
            let direction = CursorDirection.from(deltaX: dx, deltaY: dy)
            if direction != currentIdleDirection {
                currentIdleDirection = direction
                displayFrame(idleClip.image(for: direction))
            }

            if isOverOpaquePixel && !wasHoveringPet {
                if assets.hasClip(for: .drink) {
                    playManualAction(.drink)
                }
            }
        }
        wasHoveringPet = isOverOpaquePixel
    }

    private func displayFrame(_ image: NSImage?) {
        view.currentImage = image
        guard let image else { return }
        NSApp.applicationIconImage = image
        NSApp.dockTile.display()
    }

    private func resize(to size: PetSize) {
        guard size != currentSize else { return }
        let oldFrame = window.frame
        let side = size.sideLength
        let newOrigin = NSPoint(
            x: oldFrame.midX - side / 2,
            y: oldFrame.midY - side / 2
        )
        window.setFrame(NSRect(x: newOrigin.x, y: newOrigin.y, width: side, height: side), display: true, animate: true)
        currentSize = size
        userDidInteract()
    }

    private func ensureWindowIsOnScreen() {
        guard let screen = NSScreen.screens.first(where: { $0.frame.intersects(window.frame) }) ?? NSScreen.main else { return }
        let visible = screen.visibleFrame
        var origin = window.frame.origin
        origin.x = min(max(origin.x, visible.minX), visible.maxX - window.frame.width)
        origin.y = min(max(origin.y, visible.minY), visible.maxY - window.frame.height)
        window.setFrameOrigin(origin)
    }
}
