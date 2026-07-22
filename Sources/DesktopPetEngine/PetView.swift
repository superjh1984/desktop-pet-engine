import AppKit

final class PetView: NSView {
    weak var controller: PetController?

    var currentImage: NSImage? {
        didSet {
            if let image = currentImage,
               let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) {
                currentBitmap = NSBitmapImageRep(cgImage: cgImage)
            } else {
                currentBitmap = nil
            }
            needsDisplay = true
        }
    }

    private var currentBitmap: NSBitmapImageRep?
    private var mouseDownScreenPoint: NSPoint?
    private var windowOriginAtMouseDown: NSPoint?
    private var didDrag = false
    private let messageLabel = NSTextField(labelWithString: "")
    private var messageWorkItem: DispatchWorkItem?

    override var isFlipped: Bool { true }
    override var acceptsFirstResponder: Bool { true }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        layer?.backgroundColor = NSColor.clear.cgColor

        messageLabel.alignment = .center
        messageLabel.textColor = .white
        messageLabel.font = .systemFont(ofSize: 12, weight: .semibold)
        messageLabel.backgroundColor = NSColor.black.withAlphaComponent(0.72)
        messageLabel.drawsBackground = true
        messageLabel.isBordered = false
        messageLabel.isHidden = true
        messageLabel.wantsLayer = true
        messageLabel.layer?.cornerRadius = 8
        addSubview(messageLabel)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func layout() {
        super.layout()
        let width = min(bounds.width - 24, max(120, messageLabel.intrinsicContentSize.width + 24))
        messageLabel.frame = NSRect(
            x: (bounds.width - width) / 2,
            y: 12,
            width: width,
            height: 28
        )
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        currentImage?.draw(
            in: bounds,
            from: .zero,
            operation: .sourceOver,
            fraction: 1,
            respectFlipped: true,
            hints: [.interpolation: NSNumber(value: NSImageInterpolation.high.rawValue)]
        )
    }

    func showMessage(_ text: String, duration: TimeInterval = 1.5) {
        messageWorkItem?.cancel()
        messageLabel.stringValue = text
        messageLabel.isHidden = false
        needsLayout = true

        let workItem = DispatchWorkItem { [weak self] in
            self?.messageLabel.isHidden = true
        }
        messageWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + duration, execute: workItem)
    }

    func containsOpaquePixel(atWindowPoint point: NSPoint) -> Bool {
        guard bounds.width > 0, bounds.height > 0,
              let bitmap = currentBitmap else { return false }
        let local = convert(point, from: nil)
        guard bounds.contains(local) else { return false }

        let x = min(bitmap.pixelsWide - 1, max(0, Int(local.x / bounds.width * CGFloat(bitmap.pixelsWide))))
        let flippedY = bounds.height - local.y
        let y = min(bitmap.pixelsHigh - 1, max(0, Int(flippedY / bounds.height * CGFloat(bitmap.pixelsHigh))))
        return (bitmap.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0.10
    }

    override func mouseDown(with event: NSEvent) {
        guard containsOpaquePixel(atWindowPoint: event.locationInWindow), let window else { return }
        mouseDownScreenPoint = NSEvent.mouseLocation
        windowOriginAtMouseDown = window.frame.origin
        didDrag = false
    }

    override func mouseDragged(with event: NSEvent) {
        guard let window,
              let startMouse = mouseDownScreenPoint,
              let startOrigin = windowOriginAtMouseDown else { return }
        let current = NSEvent.mouseLocation
        let dx = current.x - startMouse.x
        let dy = current.y - startMouse.y
        if hypot(dx, dy) > 3 { didDrag = true }
        window.setFrameOrigin(NSPoint(x: startOrigin.x + dx, y: startOrigin.y + dy))
        controller?.userDidInteract()
    }

    override func mouseUp(with event: NSEvent) {
        defer {
            mouseDownScreenPoint = nil
            windowOriginAtMouseDown = nil
            didDrag = false
        }
        guard !didDrag else {
            controller?.userDidInteract()
            return
        }
        controller?.handleLeftClick(clickCount: event.clickCount)
    }

    override func rightMouseDown(with event: NSEvent) {
        guard containsOpaquePixel(atWindowPoint: event.locationInWindow) else { return }
        controller?.userDidInteract()
        guard let menu = controller?.makeContextMenu() else { return }
        NSMenu.popUpContextMenu(menu, with: event, for: self)
    }
}
