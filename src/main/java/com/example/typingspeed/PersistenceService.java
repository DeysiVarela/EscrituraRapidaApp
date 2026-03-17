package com.example.typingspeed;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Simple persistence service that appends results to `results.json`
 * and reads all lines back. The file stores one JSON-like line per result.
 */
public class PersistenceService {
    private static final PersistenceService INSTANCE = new PersistenceService();
    private final Path path = Path.of("results.json");

    private PersistenceService() { }

    public static PersistenceService getInstance() {
        return INSTANCE;
    }

    public synchronized void save(GameResult r) {
        try {
            String line = String.format("{\"time\":\"%s\",\"score\":%d}%n", r.getTimestamp().toString(), r.getScore());
            Files.writeString(path, line, java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch (IOException ex) {
            // swallow for now; controllers will show UI feedback
        }
    }

    public synchronized List<String> readAll() {
        try {
            if (!Files.exists(path)) return new ArrayList<>();
            return Files.readAllLines(path).stream().collect(Collectors.toList());
        } catch (IOException ex) {
            return List.of("<error reading results>");
        }
    }
}
