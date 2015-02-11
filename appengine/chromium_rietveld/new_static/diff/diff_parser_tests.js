// Copyright (c) 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

"use strict";

describe("DiffParser", function() {
    it("should detect image file names", function() {
        expect(DiffParser.isImageFile("foo.png")).toBeTruthy();
        expect(DiffParser.isImageFile("foo.bar.jpeg")).toBeTruthy();
        expect(DiffParser.isImageFile("foo(baz).jpg")).toBeTruthy();
        expect(DiffParser.isImageFile("_foo_.webp")).toBeTruthy();
        expect(DiffParser.isImageFile("example-file-name.bmp")).toBeTruthy();
        expect(DiffParser.isImageFile("is a. gif.gif")).toBeTruthy();
        expect(DiffParser.isImageFile(".gif")).toBeFalsy();
        expect(DiffParser.isImageFile("not a gif.gif.txt")).toBeFalsy();
    });
    it("should not show context link for file deletes", function() {
        var text =
            "Index: example.cc\n" +
            "diff --git a/example.cc b/example.cc\n" +
            "index aaf..def 100644\n" +
            "--- a/example.cc\n" +
            "+++ b/example.cc\n" +
            "@@ -1,1 +0,0 @@ File deleted\n" +
            "- This was a line\n";
        var parser = new DiffParser(text);
        var result = parser.parse()[0];
        expect(result.name).toBe("example.cc");
        expect(result.groups.length).toBe(3);
        expect(result.groups[0].length).toBe(1);
        expect(result.groups[0][0].type).toBe("header");
        expect(result.groups[0][0].context).toBe(false);
        expect(result.groups[0][0].text).toBe("File deleted");
    });
    it("should show context for one line headers", function() {
        var text =
            "Index: example.cc\n" +
            "diff --git a/example.cc b/example.cc\n" +
            "index aaf..def 100644\n" +
            "--- a/example.cc\n" +
            "+++ b/example.cc\n" +
            "@@ -1,2 +1,1 @@ Context 1\n" +
            " A line of text\n" +
            "- Example line 1\n" +
            "@@ -4,2 +3,1 @@ Context 2\n" +
            " A line of text\n" +
            "- Example line 1\n";
        var parser = new DiffParser(text);
        var result = parser.parse()[0];
        expect(result.name).toBe("example.cc");
        expect(result.groups.length).toBe(7);
        expect(result.groups[0].length).toBe(1);
        expect(result.groups[0][0].type).toBe("header");
        expect(result.groups[0][0].context).toBe(false);
        expect(result.groups[0][0].text).toBe("Context 1");
        expect(result.groups[3].length).toBe(1);
        expect(result.groups[3][0].type).toBe("header");
        expect(result.groups[3][0].context).toBe(true);
        expect(result.groups[3][0].text).toBe("Context 2");
    });
    it("should skip lines with backslash prefixes", function() {
        var text =
            "Index: example.cc\n" +
            "diff --git a/example.cc b/example.cc\n" +
            "index aaf..def 100644\n" +
            "--- a/example.cc\n" +
            "+++ b/example.cc\n" +
            "@@ -1,2 +1,2 @@ Context 1\n" +
            " A line of text\n" +
            "-Example line 1\n" +
            "\\ No newline at end of file\n" +
            "+Example line 2\n";
        var parser = new DiffParser(text);
        var result = parser.parse()[0];
        expect(result.name).toBe("example.cc");
        expect(result.groups.length).toBe(4);
        expect(result.groups[0].length).toBe(1);
        expect(result.groups[0][0].type).toBe("header");
        expect(result.groups[0][0].context).toBe(false);
        expect(result.groups[0][0].text).toBe("Context 1");
        expect(result.groups[2].length).toBe(2);
        expect(result.groups[2][0].type).toBe("remove");
        expect(result.groups[2][0].text).toBe("Example line 1");
        expect(result.groups[2][1].type).toBe("add");
        expect(result.groups[2][1].text).toBe("Example line 2");
    });
});