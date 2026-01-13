#!/usr/bin/swift

import Foundation
import EventKit

// Command line arguments
let args = CommandLine.arguments
var operation = "calendars"  // Default operation
var calendarName: String? = nil
var startDateStr: String? = nil
var endDateStr: String? = nil
var icsFilePath: String? = nil

// Parse arguments
var i = 1
while i < args.count {
    switch args[i] {
    case "--calendars":
        operation = "calendars"
    case "--events":
        operation = "events"
    case "--delete-events":
        operation = "delete-events"
    case "--import-ics":
        operation = "import-ics"
    case "--calendar":
        i += 1
        if i < args.count {
            calendarName = args[i]
        }
    case "--start-date":
        i += 1
        if i < args.count {
            startDateStr = args[i]
        }
    case "--end-date":
        i += 1
        if i < args.count {
            endDateStr = args[i]
        }
    case "--ics-file":
        i += 1
        if i < args.count {
            icsFilePath = args[i]
        }
    default:
        break
    }
    i += 1
}

// Setup date formatter
let dateFormatter = DateFormatter()
dateFormatter.dateFormat = "yyyy-MM-dd"
dateFormatter.timeZone = TimeZone.current

// Parse dates
let startDate: Date
if let dateStr = startDateStr, let date = dateFormatter.date(from: dateStr) {
    startDate = date
} else {
    startDate = Date() // Today
}

let endDate: Date
if let dateStr = endDateStr, let date = dateFormatter.date(from: dateStr) {
    endDate = date
} else {
    // Default to 30 days ahead
    endDate = Calendar.current.date(byAdding: .day, value: 30, to: startDate)!
}

// Output date formatter (for event dates)
let outputDateFormatter = DateFormatter()
outputDateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
outputDateFormatter.timeZone = TimeZone.current

// EventKit store
let eventStore = EKEventStore()

// Group for waiting for async permission request
let group = DispatchGroup()
group.enter()

// Request access to calendar
eventStore.requestAccess(to: .event) { (granted, error) in
    if granted {
        do {
            // Prepare output JSON
            var outputDict: [String: Any] = [:]
            
            switch operation {
            case "calendars":
                let calendars = eventStore.calendars(for: .event)
                var calendarList: [[String: Any]] = []
                
                for calendar in calendars {
                    let calendarDict: [String: Any] = [
                        "title": calendar.title,
                        "id": calendar.calendarIdentifier,
                        "type": calendar.type.rawValue,
                        "source": calendar.source.title
                    ]
                    calendarList.append(calendarDict)
                }
                outputDict["calendars"] = calendarList
            
            case "delete-events":
                guard let name = calendarName else {
                    outputDict["error"] = "Calendar name required for delete operation"
                    break
                }
                
                // Find the calendar
                let calendarsToDelete = eventStore.calendars(for: .event).filter { $0.title == name }
                guard let targetCalendar = calendarsToDelete.first else {
                    outputDict["error"] = "Calendar '\(name)' not found"
                    break
                }
                
                // Get all events from the calendar
                let predicate = eventStore.predicateForEvents(withStart: startDate, end: endDate, calendars: [targetCalendar])
                let events = eventStore.events(matching: predicate)
                
                var deletedCount = 0
                var errors: [String] = []
                
                for event in events {
                    do {
                        try eventStore.remove(event, span: .thisEvent, commit: false)
                        deletedCount += 1
                    } catch {
                        errors.append("Failed to delete event '\(event.title ?? "Unknown")': \(error.localizedDescription)")
                    }
                }
                
                // Commit all deletions at once
                do {
                    try eventStore.commit()
                    outputDict["success"] = true
                    outputDict["deleted_count"] = deletedCount
                    if !errors.isEmpty {
                        outputDict["errors"] = errors
                    }
                } catch {
                    outputDict["error"] = "Failed to commit deletions: \(error.localizedDescription)"
                }
            
            case "import-ics":
                guard let name = calendarName else {
                    outputDict["error"] = "Calendar name required for import operation"
                    break
                }
                
                guard let icsPath = icsFilePath else {
                    outputDict["error"] = "ICS file path required for import operation"
                    break
                }
                
                // Find the calendar
                let calendarsToImport = eventStore.calendars(for: .event).filter { $0.title == name }
                guard let targetCalendar = calendarsToImport.first else {
                    outputDict["error"] = "Calendar '\(name)' not found"
                    break
                }
                
                // Check if calendar is writable
                guard targetCalendar.allowsContentModifications else {
                    outputDict["error"] = "Calendar '\(name)' is read-only"
                    break
                }
                
                // Read ICS file
                guard let icsData = try? String(contentsOfFile: icsPath, encoding: .utf8) else {
                    outputDict["error"] = "Failed to read ICS file at '\(icsPath)'"
                    break
                }
                
                var importedCount = 0
                var errors: [String] = []
                
                // Parse ICS file (basic parsing)
                let lines = icsData.components(separatedBy: .newlines)
                var currentEvent: EKEvent? = nil
                
                for line in lines {
                    let trimmedLine = line.trimmingCharacters(in: .whitespaces)
                    
                    if trimmedLine == "BEGIN:VEVENT" {
                        currentEvent = EKEvent(eventStore: eventStore)
                        currentEvent?.calendar = targetCalendar
                    } else if trimmedLine == "END:VEVENT" {
                        if let event = currentEvent {
                            do {
                                try eventStore.save(event, span: .thisEvent, commit: false)
                                importedCount += 1
                            } catch {
                                errors.append("Failed to import event: \(error.localizedDescription)")
                            }
                        }
                        currentEvent = nil
                    } else if let event = currentEvent {
                        // Parse event properties
                        if trimmedLine.hasPrefix("SUMMARY:") {
                            event.title = String(trimmedLine.dropFirst("SUMMARY:".count))
                        } else if trimmedLine.hasPrefix("DTSTART") {
                            parseEventDate(line: trimmedLine, event: event, isStart: true, dateFormatter: dateFormatter)
                        } else if trimmedLine.hasPrefix("DTEND") {
                            parseEventDate(line: trimmedLine, event: event, isStart: false, dateFormatter: dateFormatter)
                        } else if trimmedLine.hasPrefix("LOCATION:") {
                            event.location = String(trimmedLine.dropFirst("LOCATION:".count))
                        } else if trimmedLine.hasPrefix("DESCRIPTION:") {
                            event.notes = String(trimmedLine.dropFirst("DESCRIPTION:".count))
                        } else if trimmedLine.hasPrefix("URL:") {
                            if let url = URL(string: String(trimmedLine.dropFirst("URL:".count))) {
                                event.url = url
                            }
                        }
                    }
                }
                
                // Commit all imports at once
                do {
                    try eventStore.commit()
                    outputDict["success"] = true
                    outputDict["imported_count"] = importedCount
                    if !errors.isEmpty {
                        outputDict["errors"] = errors
                    }
                } catch {
                    outputDict["error"] = "Failed to commit imports: \(error.localizedDescription)"
                }
                
            case "events":
                var targetCalendars: [EKCalendar]?
                
                if let name = calendarName {
                    // Filter calendars by name
                    targetCalendars = eventStore.calendars(for: .event).filter { $0.title == name }
                    if targetCalendars?.isEmpty ?? true {
                        print("Error: Calendar '\(name)' not found")
                        exit(1)
                    }
                }
                
                let predicate = eventStore.predicateForEvents(withStart: startDate, end: endDate, calendars: targetCalendars)
                let events = eventStore.events(matching: predicate)
                
                var eventList: [[String: Any]] = []
                for event in events {
                    var eventDict: [String: Any] = [
                        "event_id": event.eventIdentifier ?? UUID().uuidString,
                        "calendar_name": event.calendar.title,
                        "title": event.title ?? "(No Title)",
                        "start_date": outputDateFormatter.string(from: event.startDate),
                        "end_date": outputDateFormatter.string(from: event.endDate),
                        "all_day": event.isAllDay
                    ]
                    
                    if let loc = event.location, !loc.isEmpty {
                        eventDict["location"] = loc
                    }
                    
                    if let notes = event.notes, !notes.isEmpty {
                        eventDict["description"] = notes
                    }
                    
                    if let url = event.url?.absoluteString {
                        eventDict["url"] = url
                    }
                    
                    eventList.append(eventDict)
                }
                
                outputDict["events"] = eventList
                outputDict["start_date"] = outputDateFormatter.string(from: startDate)
                outputDict["end_date"] = outputDateFormatter.string(from: endDate)
                if let name = calendarName {
                    outputDict["calendar_name"] = name
                }
            default:
                outputDict["error"] = "Unknown operation"
            }
            
            // Convert to JSON and print
            let jsonData = try JSONSerialization.data(withJSONObject: outputDict, options: .prettyPrinted)
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print(jsonString)
            }
        } catch {
            print("Error: \(error.localizedDescription)")
        }
    } else {
        // Output error as JSON for better parsing
        var errorDict: [String: Any] = [
            "error": "Access denied to calendar",
            "message": error?.localizedDescription ?? "Unknown error"
        ]
        if let error = error {
            errorDict["error_code"] = (error as NSError).code
            errorDict["error_domain"] = (error as NSError).domain
        }
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: errorDict, options: [])
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print(jsonString)
            }
        } catch {
            print("{\"error\": \"Access denied or error: \(String(describing: error))\"}")
        }
    }
    
    group.leave()
}

// Wait for the async operation to complete
group.wait()

// Helper function to parse event dates from ICS format
func parseEventDate(line: String, event: EKEvent, isStart: Bool, dateFormatter: DateFormatter) {
    // Extract date value after the colon
    guard let colonIndex = line.firstIndex(of: ":") else { return }
    let dateValue = String(line[line.index(after: colonIndex)...])
    
    // Check if it's an all-day event
    let isAllDay = line.contains(";VALUE=DATE")
    
    let dateFormat: String
    if isAllDay {
        dateFormat = "yyyyMMdd"
    } else if dateValue.hasSuffix("Z") {
        dateFormat = "yyyyMMdd'T'HHmmss'Z'"
    } else {
        dateFormat = "yyyyMMdd'T'HHmmss"
    }
    
    let parser = DateFormatter()
    parser.dateFormat = dateFormat
    parser.timeZone = isAllDay ? TimeZone(identifier: "UTC") : TimeZone.current
    
    if let date = parser.date(from: dateValue) {
        if isStart {
            event.startDate = date
        } else {
            event.endDate = date
        }
        event.isAllDay = isAllDay
    }
}
