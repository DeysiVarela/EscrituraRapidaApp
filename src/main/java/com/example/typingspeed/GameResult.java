package com.example.typingspeed;

import java.time.Instant;

/**
 * Simple data model representing a finished game result.
 */
public class GameResult {
    private final Instant timestamp;
    private final int score;

    public GameResult(Instant timestamp, int score) {
        this.timestamp = timestamp;
        this.score = score;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public int getScore() {
        return score;
    }

    @Override
    public String toString() {
        return String.format("%s — score: %d", timestamp.toString(), score);
    }
}
