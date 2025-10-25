"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar as CalendarIcon, Clock, Plus, RefreshCw } from "lucide-react";
import { format, parseISO } from "date-fns";

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  location?: string;
  google_event_id?: string;
  created_at: string;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch events from backend
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/calendar/events`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch events');
      }

      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      console.error('Error fetching events:', err);
      setError('Failed to load events. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (datetime: string) => {
    try {
      return format(parseISO(datetime), 'MMM dd, yyyy h:mm a');
    } catch {
      return datetime;
    }
  };

  const formatTime = (datetime: string) => {
    try {
      return format(parseISO(datetime), 'h:mm a');
    } catch {
      return datetime;
    }
  };

  const getUpcomingEvents = () => {
    const now = new Date();
    return events.filter(event => new Date(event.start_time) >= now);
  };

  const getPastEvents = () => {
    const now = new Date();
    return events.filter(event => new Date(event.start_time) < now);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            📅 Calendar
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your meetings and events
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchEvents} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{events.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Upcoming
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {getUpcomingEvents().length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Past Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-400">
              {getPastEvents().length}
            </div>
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-8 text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchEvents} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      ) : events.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <CalendarIcon className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Events Yet</h3>
            <p className="text-gray-600 mb-4">
              Ask Zyana to create events via Telegram
            </p>
            <p className="text-sm text-gray-500">
              Try: "Book meeting tomorrow at 10am with John"
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Upcoming Events */}
          {getUpcomingEvents().length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Clock className="w-6 h-6 text-green-600" />
                Upcoming Events
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {getUpcomingEvents().map((event) => (
                  <Card 
                    key={event.id}
                    className="hover:shadow-lg transition-shadow border-l-4 border-l-green-500"
                  >
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <CardTitle className="text-xl mb-2">
                            {event.title}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-4">
                            <span className="flex items-center gap-1">
                              <CalendarIcon className="w-4 h-4" />
                              {formatDateTime(event.start_time)}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {formatTime(event.start_time)} - {formatTime(event.end_time)}
                            </span>
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          {event.google_event_id && (
                            <Badge variant="outline" className="bg-blue-50">
                              🔗 Synced
                            </Badge>
                          )}
                          <Badge className="bg-green-100 text-green-800">
                            Upcoming
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    {event.description && (
                      <CardContent>
                        <p className="text-gray-600">{event.description}</p>
                        {event.location && (
                          <p className="text-sm text-gray-500 mt-2">
                            📍 {event.location}
                          </p>
                        )}
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Past Events */}
          {getPastEvents().length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2 text-gray-500">
                <CalendarIcon className="w-6 h-6" />
                Past Events
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {getPastEvents().map((event) => (
                  <Card 
                    key={event.id}
                    className="opacity-75 border-l-4 border-l-gray-300"
                  >
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <CardTitle className="text-xl mb-2 text-gray-600">
                            {event.title}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-4">
                            <span className="flex items-center gap-1">
                              <CalendarIcon className="w-4 h-4" />
                              {formatDateTime(event.start_time)}
                            </span>
                          </CardDescription>
                        </div>
                        <Badge variant="outline" className="bg-gray-100">
                          Past
                        </Badge>
                      </div>
                    </CardHeader>
                    {event.description && (
                      <CardContent>
                        <p className="text-gray-500">{event.description}</p>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Help Text */}
      <Card className="mt-8 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-lg">💡 How to Create Events</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-2">Message your Telegram bot with:</p>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            <li>"Book meeting tomorrow at 10am"</li>
            <li>"Schedule call with John on Friday at 3pm"</li>
            <li>"Meeting in next 30 minutes"</li>
            <li>"Appointment next Monday at 2pm"</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

