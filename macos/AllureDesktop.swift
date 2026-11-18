import Cocoa
import WebKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, WKUIDelegate {
    var window:NSWindow!
    var browser:WKWebView!
    func applicationDidFinishLaunching(_ notification:Notification) {
        let appMenu=NSMenu();let root=NSMenuItem();appMenu.addItem(root);let submenu=NSMenu();submenu.addItem(withTitle:"Quit ALLURÉ",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q");root.submenu=submenu;NSApp.mainMenu=appMenu
        window=NSWindow(contentRect:NSRect(x:0,y:0,width:1280,height:860),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title="ALLURÉ — Your personal atelier";window.minSize=NSSize(width:390,height:650);window.center()
        let configuration=WKWebViewConfiguration();configuration.websiteDataStore = .default()
        browser=WKWebView(frame:.zero,configuration:configuration);browser.uiDelegate=self;browser.allowsBackForwardNavigationGestures=true;window.contentView=browser
        let url=Bundle.main.object(forInfoDictionaryKey:"AllureWebsiteURL") as? String ?? "http://localhost:8790"
        browser.load(URLRequest(url:URL(string:url)!));window.makeKeyAndOrderFront(nil);NSApp.activate(ignoringOtherApps:true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool {true}
    func webView(_ webView:WKWebView,runOpenPanelWith parameters:WKOpenPanelParameters,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping([URL]?)->Void) {
        let panel=NSOpenPanel();panel.canChooseDirectories=false;panel.allowsMultipleSelection=parameters.allowsMultipleSelection
        panel.begin { response in completionHandler(response == .OK ? panel.urls : nil) }
    }
    func webView(_ webView:WKWebView,runJavaScriptAlertPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping()->Void) {let alert=NSAlert();alert.messageText="ALLURÉ";alert.informativeText=message;alert.addButton(withTitle:"OK");alert.runModal();completionHandler()}
    func webView(_ webView:WKWebView,runJavaScriptConfirmPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping(Bool)->Void) {let alert=NSAlert();alert.messageText="ALLURÉ";alert.informativeText=message;alert.addButton(withTitle:"Confirm");alert.addButton(withTitle:"Cancel");completionHandler(alert.runModal() == .alertFirstButtonReturn)}
}
@main struct AllureDesktop {
    @MainActor static func main() {let app=NSApplication.shared;let delegate=AppDelegate();app.delegate=delegate;app.setActivationPolicy(.regular);app.run()}
}
