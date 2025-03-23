package com.example.commitmessagegenerator.Util;


import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

@Component
public class FileUtil {

    public List<String> readLines(Path filePath) throws IOException {
        return Files.readAllLines(filePath);
    }
}
