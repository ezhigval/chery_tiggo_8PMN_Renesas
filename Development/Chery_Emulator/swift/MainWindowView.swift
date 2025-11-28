import SwiftUI

private enum ControlTab: String, CaseIterable, Identifiable {
    case vehicle = "Vehicle"
    case cabin = "Cabin"
    case steering = "Steering_Wheel"
    case infotainment = "Infotainment"
    case system = "System"

    var id: String { rawValue }
}

struct MainWindowView: View {
    @EnvironmentObject private var coreClient: CoreClient
    @State private var selectedTab: ControlTab = .vehicle

    var body: some View {
        NavigationView {
            sidebar
            content
        }
        .navigationTitle("Chery Emulator")
        .task {
            await coreClient.refreshState()
        }
    }

    private var sidebar: some View {
        List(selection: $selectedTab) {
            Section("Panels") {
                ForEach(ControlTab.allCases) { tab in
                    Text(tab.rawValue)
                        .tag(tab)
                }
            }
        }
        .listStyle(SidebarListStyle())
    }

    private var content: some View {
        VStack(spacing: 16) {
            HStack(alignment: .top, spacing: 16) {
                huDisplay
                clusterDisplay
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            controlPanel
        }
        .padding()
    }

    private var huDisplay: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.black)
            Text("HU Display")
                .foregroundColor(.white.opacity(0.7))
        }
        .aspectRatio(1920.0 / 720.0, contentMode: .fit)
    }

    private var clusterDisplay: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(red: 0.05, green: 0.05, blue: 0.08))
            Text("Cluster Display")
                .foregroundColor(.white.opacity(0.7))
        }
        .aspectRatio(2.5, contentMode: .fit)
        .frame(maxWidth: 400)
    }

    private var controlPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Ignition state:")
                    .font(.headline)
                Text(coreClient.ignitionState)
                    .font(.headline)
                    .foregroundColor(.green)
            }

            HStack(spacing: 16) {
                Button("Ignition short press") {
                    Task { await coreClient.ignitionPressShort() }
                }
                Button("Ignition long press") {
                    Task { await coreClient.ignitionPressLong() }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct MainWindowView_Previews: PreviewProvider {
    static var previews: some View {
        MainWindowView()
            .environmentObject(CoreClient())
            .frame(width: 1400, height: 800)
    }
}
