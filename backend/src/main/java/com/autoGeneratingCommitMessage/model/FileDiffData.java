package com.autoGeneratingCommitMessage.model;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class FileDiffData {

  private String file;
  private String diff;

  public FileDiffData(String file, String diff) {
    this.file = file;
    this.diff = diff;
  }

}
