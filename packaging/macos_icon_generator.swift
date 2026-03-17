import AppKit

let outputPath = CommandLine.arguments[1]
let size = CGFloat(1024.0)

func roundedRect(_ rect: NSRect, radius: CGFloat) -> NSBezierPath {
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
}

func drawGradient(in path: NSBezierPath, colors: [NSColor], angle: CGFloat) {
    guard let gradient = NSGradient(colors: colors) else { return }
    NSGraphicsContext.saveGraphicsState()
    path.addClip()
    gradient.draw(in: path, angle: angle)
    NSGraphicsContext.restoreGraphicsState()
}

func fill(_ path: NSBezierPath, color: NSColor) {
    color.setFill()
    path.fill()
}

func stroke(_ path: NSBezierPath, color: NSColor, width: CGFloat) {
    color.setStroke()
    path.lineWidth = width
    path.stroke()
}

func bubblePath(body: NSRect, tail: NSRect, radius: CGFloat, tailRadius: CGFloat) -> NSBezierPath {
    let path = NSBezierPath()
    path.append(roundedRect(body, radius: radius))
    path.append(roundedRect(tail, radius: tailRadius))
    return path
}

func drawShadowedShape(_ path: NSBezierPath, shadow: NSShadow) {
    NSGraphicsContext.saveGraphicsState()
    shadow.set()
    path.fill()
    NSGraphicsContext.restoreGraphicsState()
}

let image = NSImage(size: NSSize(width: size, height: size))
image.lockFocus()

guard let ctx = NSGraphicsContext.current?.cgContext else {
    fputs("Failed to access graphics context\n", stderr)
    exit(1)
}

ctx.interpolationQuality = .high

let canvas = NSRect(x: 0, y: 0, width: size, height: size)
NSColor.clear.setFill()
canvas.fill()

let outerRect = canvas.insetBy(dx: 56, dy: 56)
let outer = roundedRect(outerRect, radius: 228)
drawGradient(
    in: outer,
    colors: [
        NSColor(calibratedRed: 0.04, green: 0.08, blue: 0.16, alpha: 1.0),
        NSColor(calibratedRed: 0.06, green: 0.22, blue: 0.43, alpha: 1.0),
        NSColor(calibratedRed: 0.09, green: 0.43, blue: 0.68, alpha: 1.0),
    ],
    angle: 130
)

NSGraphicsContext.saveGraphicsState()
outer.addClip()

fill(
    NSBezierPath(ovalIn: NSRect(x: 50, y: 590, width: 520, height: 360)),
    color: NSColor(calibratedRed: 0.73, green: 0.93, blue: 1.00, alpha: 0.12)
)
fill(
    NSBezierPath(ovalIn: NSRect(x: 470, y: 90, width: 420, height: 320)),
    color: NSColor(calibratedRed: 0.16, green: 0.82, blue: 0.92, alpha: 0.11)
)
fill(
    NSBezierPath(ovalIn: NSRect(x: 460, y: 640, width: 420, height: 300)),
    color: NSColor(calibratedRed: 0.90, green: 0.97, blue: 1.00, alpha: 0.10)
)

let sheen = roundedRect(NSRect(x: 122, y: 650, width: 780, height: 190), radius: 120)
fill(sheen, color: NSColor.white.withAlphaComponent(0.06))
NSGraphicsContext.restoreGraphicsState()

let border = roundedRect(outerRect.insetBy(dx: 1.5, dy: 1.5), radius: 224)
stroke(border, color: NSColor.white.withAlphaComponent(0.10), width: 3)

let rearBubble = roundedRect(NSRect(x: 178, y: 510, width: 378, height: 244), radius: 108)
let rearShadow = NSShadow()
rearShadow.shadowColor = NSColor.black.withAlphaComponent(0.16)
rearShadow.shadowBlurRadius = 24
rearShadow.shadowOffset = NSSize(width: 0, height: -10)

NSGraphicsContext.saveGraphicsState()
rearShadow.set()
drawGradient(
    in: rearBubble,
    colors: [
        NSColor(calibratedRed: 0.60, green: 0.86, blue: 1.00, alpha: 0.28),
        NSColor(calibratedRed: 0.26, green: 0.58, blue: 0.88, alpha: 0.18),
    ],
    angle: 90
)
NSGraphicsContext.restoreGraphicsState()

let frontBody = NSRect(x: 220, y: 258, width: 590, height: 438)
let frontTail = NSRect(x: 635, y: 216, width: 146, height: 124)
let frontBubble = bubblePath(body: frontBody, tail: frontTail, radius: 138, tailRadius: 54)

let frontShadow = NSShadow()
frontShadow.shadowColor = NSColor.black.withAlphaComponent(0.26)
frontShadow.shadowBlurRadius = 36
frontShadow.shadowOffset = NSSize(width: 0, height: -18)

NSGraphicsContext.saveGraphicsState()
frontShadow.set()
drawGradient(
    in: frontBubble,
    colors: [
        NSColor(calibratedRed: 0.98, green: 0.99, blue: 1.00, alpha: 1.0),
        NSColor(calibratedRed: 0.90, green: 0.94, blue: 0.98, alpha: 1.0),
    ],
    angle: 270
)
NSGraphicsContext.restoreGraphicsState()

let frontHighlight = roundedRect(NSRect(x: 262, y: 566, width: 510, height: 92), radius: 46)
fill(frontHighlight, color: NSColor.white.withAlphaComponent(0.44))
stroke(frontBubble, color: NSColor.white.withAlphaComponent(0.72), width: 3.2)

let displayRect = NSRect(x: 304, y: 366, width: 422, height: 212)
let display = roundedRect(displayRect, radius: 82)
drawGradient(
    in: display,
    colors: [
        NSColor(calibratedRed: 0.08, green: 0.16, blue: 0.27, alpha: 1.0),
        NSColor(calibratedRed: 0.07, green: 0.28, blue: 0.47, alpha: 1.0),
    ],
    angle: 90
)
fill(roundedRect(NSRect(x: 330, y: 512, width: 368, height: 42), radius: 21), color: NSColor.white.withAlphaComponent(0.08))
stroke(display, color: NSColor.white.withAlphaComponent(0.08), width: 2)

let barWidths: [CGFloat] = [42, 42, 42, 42, 42]
let barHeights: [CGFloat] = [78, 126, 174, 126, 78]
let barXs: [CGFloat] = [364, 436, 508, 580, 652]
let barBase = CGFloat(396)
let barColors = [
    NSColor(calibratedRed: 0.54, green: 0.84, blue: 1.00, alpha: 0.98),
    NSColor(calibratedRed: 0.36, green: 0.78, blue: 1.00, alpha: 1.0),
    NSColor(calibratedRed: 0.16, green: 0.91, blue: 0.84, alpha: 1.0),
    NSColor(calibratedRed: 0.36, green: 0.78, blue: 1.00, alpha: 1.0),
    NSColor(calibratedRed: 0.54, green: 0.84, blue: 1.00, alpha: 0.98),
]

for index in 0..<barXs.count {
    let rect = NSRect(x: barXs[index], y: barBase, width: barWidths[index], height: barHeights[index])
    let bar = roundedRect(rect, radius: 21)
    let barShadow = NSShadow()
    barShadow.shadowColor = barColors[index].withAlphaComponent(0.28)
    barShadow.shadowBlurRadius = 12
    barShadow.shadowOffset = .zero
    NSGraphicsContext.saveGraphicsState()
    barShadow.set()
    fill(bar, color: barColors[index])
    NSGraphicsContext.restoreGraphicsState()
}

let accent = NSBezierPath()
accent.lineWidth = 10
accent.lineCapStyle = .round
accent.move(to: NSPoint(x: 372, y: 334))
accent.curve(
    to: NSPoint(x: 660, y: 334),
    controlPoint1: NSPoint(x: 432, y: 302),
    controlPoint2: NSPoint(x: 600, y: 302)
)
stroke(accent, color: NSColor(calibratedRed: 0.16, green: 0.82, blue: 0.98, alpha: 0.65), width: 10)

let indicatorOuter = NSBezierPath(ovalIn: NSRect(x: 690, y: 608, width: 62, height: 62))
fill(indicatorOuter, color: NSColor.white.withAlphaComponent(0.88))
let indicatorInner = NSBezierPath(ovalIn: NSRect(x: 707, y: 625, width: 28, height: 28))
fill(indicatorInner, color: NSColor(calibratedRed: 0.17, green: 0.89, blue: 0.83, alpha: 1.0))

image.unlockFocus()

guard
    let tiff = image.tiffRepresentation,
    let rep = NSBitmapImageRep(data: tiff),
    let pngData = rep.representation(using: .png, properties: [:])
else {
    fputs("Failed to render icon PNG\n", stderr)
    exit(1)
}

do {
    try pngData.write(to: URL(fileURLWithPath: outputPath))
} catch {
    fputs("Failed to save icon PNG: \(error)\n", stderr)
    exit(1)
}
