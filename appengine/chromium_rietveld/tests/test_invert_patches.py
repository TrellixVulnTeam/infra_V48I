         (self.ADD_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE, 'A'),
         (self.DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE, 'D'),
         (self.RENAME_WITH_NO_CHANGES_PATCH_TEXT, 'A +'),
         (self.COPY_WITH_NO_CHANGES_PATCH_TEXT, 'A +'),
         # Binary file patches.
         (self.ADD_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE, 'A'),
         (self.DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE, 'D'),
         (self.RENAME_AND_MODIFY_BINARY_PATCH_TEXT_WITH_NEW_MODE, 'A +'),
         (self.RENAME_WITH_NO_CHANGES_BINARY_PATCH_TEXT, 'A +'),
         (self.COPY_WITH_NO_CHANGES_BINARY_PATCH_TEXT, 'A +')):
  ADD_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE = (
      'Index: file100\n'
      'diff --git a/file100 b/file100\n'
      'new file mode %s\n'
      'index 0..8ccafb210a2d79746acc7ac06ed509f8e87ddf4c\n'
      '--- /dev/null\n'
      '+++ b/file100\n'
      '@@ -0,0 +1,3 @@\n'
      '+test\n+\n+\n' % invert_patches.DEFAULT_FILE_MODE)
  DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE = (
      'Index: file100\n'
      'diff --git a/file100 b/file100\n'
      'deleted file mode %s\n'
      'index 8ccafb210a2d79746acc7ac06ed509f8e87ddf4c..0\n'
      '--- a/file100\n'
      '+++ /dev/null\n'
      '@@ -1,3 +0,0 @@\n'
      '-test\n-\n-\n' % invert_patches.DEFAULT_FILE_MODE)
  RENAME_WITH_NO_CHANGES_PATCH_TEXT = (
      'Index: file100\n'
      'diff --git a/file7 b/file100\n'
      'similarity index 100%\n'
      'rename from file7\n'
      'rename to file100\n'
  )
  COPY_WITH_NO_CHANGES_PATCH_TEXT = (
      'Index: file100\n'
      'diff --git a/file7 b/file100\n'
      'similarity index 100%\n'
      'copy from file7\n'
      'copy to file100\n'
  )
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))
                          lines, patched_lines, None, False))

  def test_get_inverted_patch_for_copy_with_no_changes(self):
    lines = ['test\n', '\n', '\n']
    patched_lines = []
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.COPY_WITH_NO_CHANGES_PATCH_TEXT,
        filename='file100')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          lines, patched_lines, ''.join(lines), False))

  def test_get_inverted_patch_for_rename_with_no_changes(self):
    lines = ['test\n', '\n', '\n']
    patched_lines = []
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.RENAME_WITH_NO_CHANGES_PATCH_TEXT,
        filename='file100')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          lines, patched_lines, ''.join(lines), False))

  def test_get_inverted_patch_for_revert_copy_with_no_changes(self):
    lines = []
    patched_lines = ['test\n', '\n', '\n']
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
        filename='file100')

    self.assertEquals(invert_patches.ADDED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.ADD_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          lines, patched_lines, ''.join(lines), False))

  def test_get_inverted_patch_for_revert_of_revert_copy_with_no_changes(self):
    lines = ['test\n', '\n', '\n']
    patched_lines = []
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.ADD_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
        filename='file100')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          lines, patched_lines, None, False))
  ADD_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE = (
      'Index: img/file.png\n'
      'diff --git a/img/file.png b/img/file.png\n'
      'new file mode %s\n'
      'index 0..8ccafb210a2d79746acc7ac06ed509f8e87ddf4c\n'
      'Binary files /dev/null and b/img/file.png differ\n' %
          invert_patches.DEFAULT_FILE_MODE)
  DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE = (
      'Index: img/file.png\n'
      'diff --git a/img/file.png b/img/file.png\n'
      'deleted file mode %s\n'
      'index 8ccafb210a2d79746acc7ac06ed509f8e87ddf4c..0\n'
      'Binary files a/img/file.png and /dev/null differ\n' %
          invert_patches.DEFAULT_FILE_MODE)
  RENAME_WITH_NO_CHANGES_BINARY_PATCH_TEXT = (
      'Index: img/file.png\n'
      'diff --git a/img/file.png b/img/file.png\n'
      'similarity index 100%\n'
      'rename from img/old.png\n'
      'rename to img/file.png')
  COPY_WITH_NO_CHANGES_BINARY_PATCH_TEXT = (
      'Index: img/file.png\n'
      'diff --git a/img/file.png b/img/file.png\n'
      'similarity index 100%\n'
      'copy from img/old.png\n'
      'copy to img/file.png')
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))
                      invert_git_patches.get_inverted_patch_text(
                          [], [], None, True))

  def test_get_inverted_patch_for_binary_copy_with_no_changes(self):
    file_data = 'test\n\n\n'
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.COPY_WITH_NO_CHANGES_BINARY_PATCH_TEXT,
        filename='img/file.png')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          [], [], file_data, True))

  def test_get_inverted_patch_for_binary_rename_with_no_changes(self):
    file_data = 'test\n\n\n'
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.RENAME_WITH_NO_CHANGES_BINARY_PATCH_TEXT,
        filename='img/file.png')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          [], [], file_data, True))

  def test_get_inverted_patch_for_binary_revert_copy_with_no_changes(self):
    file_data = 'test\n\n\n'
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
        filename='img/file.png')

    self.assertEquals(invert_patches.ADDED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.ADD_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          [], [], file_data, True))

  def test_get_inverted_for_binary_revert_of_revert_copy_with_no_changes(self):
    file_data = 'test\n\n\n'
    invert_git_patches = invert_patches.InvertGitPatches(
        patch_text=self.ADD_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
        filename='img/file.png')

    self.assertEquals(invert_patches.DELETED_STATUS,
                      invert_git_patches.inverted_patch_status)
    self.assertEquals(self.DELETE_BINARY_PATCH_TEXT_WITH_REAL_HASH_DEFAULT_MODE,
                      invert_git_patches.get_inverted_patch_text(
                          [], [], file_data, True))