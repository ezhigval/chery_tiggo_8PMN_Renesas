import Foundation

struct VehicleStateDTO: Decodable {
    let ignition_state: String
    let updated_at: String
}

struct ActionResponseDTO: Decodable {
    let status: String
    let ignition_state: String
}

@MainActor
final class CoreClient: ObservableObject {
    @Published var ignitionState: String = "OFF"
    @Published var lastUpdated: Date? = nil

    private let baseURL: URL
    private let urlSession: URLSession

    init(baseURL: URL = URL(string: "http://127.0.0.1:8088")!,
         urlSession: URLSession = .shared) {
        self.baseURL = baseURL
        self.urlSession = urlSession
    }

    func refreshState() async {
        do {
            let url = baseURL.appendingPathComponent("state")
            let (data, _) = try await urlSession.data(from: url)
            let dto = try JSONDecoder().decode(VehicleStateDTO.self, from: data)
            ignitionState = dto.ignition_state
            lastUpdated = ISO8601DateFormatter().date(from: dto.updated_at)
        } catch {
            // For now just keep the last known state.
            print("[CoreClient] Failed to refresh state: \(error)")
        }
    }

    func ignitionPressShort() async {
        await sendIgnitionAction(path: "ignition/press_short")
    }

    func ignitionPressLong() async {
        await sendIgnitionAction(path: "ignition/press_long")
    }

    private func sendIgnitionAction(path: String) async {
        do {
            var request = URLRequest(url: baseURL.appendingPathComponent(path))
            request.httpMethod = "POST"
            let (data, _) = try await urlSession.data(for: request)
            let dto = try JSONDecoder().decode(ActionResponseDTO.self, from: data)
            ignitionState = dto.ignition_state
            lastUpdated = Date()
        } catch {
            print("[CoreClient] Failed to send ignition action (\(path)): \(error)")
        }
    }
}
