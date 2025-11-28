import SwiftUI

@main
struct CheryEmulatorApp: App {
    @StateObject private var coreClient = CoreClient()

    var body: some Scene {
        WindowGroup {
            MainWindowView()
                .environmentObject(coreClient)
        }
    }
}
