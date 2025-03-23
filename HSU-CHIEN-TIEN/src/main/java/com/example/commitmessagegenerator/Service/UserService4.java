package com.example.commitmessagegenerator.Service;

public class UserService4 {
    public String getUserName(int userId) {
        return "User-" + userId + "-v2";
    }

    public int getUserAge(int userId) {
        return userId * 2;
    }
}