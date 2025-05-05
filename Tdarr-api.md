{
  "swagger": "2.0",
  "info": {
    "title": "Tdarr API",
    "description": "Tdarr API Docs",
    "version": "2"
  },
  "definitions": {

  },
  "paths": {
    "/api/v2/add-audio-codec-exclude": {
      "post": {
        "description": "For adding an audio codec to be excluded/included in basic audio transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/add-plugin-include": {
      "post": {
        "description": "For adding a plugin to a classic plugin stack",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    },
                    "source": {
                      "type": "string"
                    },
                    "index": {
                      "type": "integer"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele",
                    "source",
                    "index"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/add-video-codec-exclude": {
      "post": {
        "description": "For adding an video codec to be excluded/included in basic video transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/admin/register": {
      "post": {
        "description": "For admin registering a new user",
        "tags": [
          "users"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "username": {
                  "type": "string"
                },
                "roles": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": [
                "username",
                "roles"
              ]
            }
          }
        ],
        "responses": {
          "201": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "temporaryPassword": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/admin/reset-password": {
      "post": {
        "description": "For admin resetting a user password",
        "tags": [
          "users"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "username": {
                  "type": "string"
                }
              },
              "required": [
                "username"
              ]
            }
          }
        ],
        "responses": {
          "201": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "temporaryPassword": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/alter-worker-limit": {
      "post": {
        "description": "For changing the number of running workers of a specific type on a specific node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "nodeID": {
                      "type": [
                        "string"
                      ]
                    },
                    "process": {
                      "type": "string",
                      "enum": [
                        "increase",
                        "decrease"
                      ]
                    },
                    "workerType": {
                      "type": "string",
                      "enum": [
                        "healthcheckcpu",
                        "healthcheckgpu",
                        "transcodecpu",
                        "transcodegpu"
                      ]
                    }
                  },
                  "required": [
                    "nodeID",
                    "process",
                    "workerType"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/auth/logout": {
      "post": {
        "description": "For logging out a user",
        "tags": [
          "users"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/auth/reset-password": {
      "post": {
        "description": "For resetting a user password",
        "tags": [
          "users"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "oldPassword": {
                  "type": "string"
                },
                "password": {
                  "type": "string"
                }
              },
              "required": [
                "oldPassword",
                "password"
              ]
            }
          }
        ],
        "responses": {
          "201": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "token": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "401": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/auth/verify-token": {
      "get": {
        "description": "For verifying a user token",
        "tags": [
          "users"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "roles": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/auth-status": {
      "post": {
        "description": "For checking Tdarr Pro status",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "saU": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "saU"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "boolean"
            }
          }
        }
      }
    },
    "/api/v2/cancel-worker-item": {
      "post": {
        "description": "For cancelling a running worker item on a specific node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    },
                    "workerID": {
                      "type": "string"
                    },
                    "cause": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "nodeID",
                    "workerID",
                    "cause"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/client/{clientType}": {
      "post": {
        "description": "For loading and updating data in various tables found around the Tdarr UI",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "start": {
                      "type": "number"
                    },
                    "pageSize": {
                      "type": "number"
                    },
                    "filters": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "type": "string"
                          },
                          "value": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "id",
                          "value"
                        ]
                      }
                    },
                    "sorts": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "type": "string"
                          },
                          "desc": {
                            "type": "boolean"
                          }
                        },
                        "required": [
                          "id",
                          "desc"
                        ]
                      }
                    },
                    "opts": {
                      "type": "object",
                      "properties": {
                        "table": {
                          "type": "string"
                        },
                        "property": {
                          "type": "string"
                        },
                        "fileMedium": {
                          "type": "string"
                        },
                        "detail": {
                          "type": "string"
                        },
                        "dbID": {
                          "type": "string"
                        },
                        "setAll": {
                          "type": "boolean"
                        },
                        "updatedObj": {
                          "type": "object"
                        },
                        "csv": {
                          "type": "boolean"
                        },
                        "applyToAllStaged": {
                          "type": "boolean"
                        },
                        "verdict": {
                          "type": "string"
                        }
                      }
                    }
                  },
                  "required": [
                    "start",
                    "pageSize",
                    "filters",
                    "sorts",
                    "opts"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          },
          {
            "type": "string",
            "required": true,
            "in": "path",
            "name": "clientType"
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/copy-community-to-local": {
      "post": {
        "description": "For copying a community plugin to local plugins",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "pluginID": {
                      "type": "string"
                    },
                    "forceOverwrite": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "pluginID",
                    "forceOverwrite"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/create-backup": {
      "post": {
        "description": "For creating a backup of the Tdarr database",
        "tags": [
          "backups"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "boolean"
            }
          }
        }
      }
    },
    "/api/v2/create-plugin": {
      "post": {
        "description": "For creating a basic classic plugin using the classic plugin creator",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "details": {
                      "type": "object",
                      "properties": {
                        "Name": {
                          "type": "string"
                        },
                        "Type": {
                          "type": "string"
                        },
                        "Operation": {
                          "type": "string"
                        },
                        "Description": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "Name",
                        "Type",
                        "Operation",
                        "Description"
                      ]
                    },
                    "conditionalsString": {
                      "type": "string"
                    },
                    "conditionalNotes": {
                      "type": "string"
                    },
                    "action": {
                      "type": "object",
                      "properties": {
                        "preset": {
                          "type": "string"
                        },
                        "container": {
                          "type": "string"
                        },
                        "handbrakeMode": {
                          "type": "boolean"
                        },
                        "ffmpegMode": {
                          "type": "boolean"
                        },
                        "processFile": {
                          "type": [
                            "boolean",
                            "string"
                          ]
                        },
                        "infoLog": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "preset",
                        "container",
                        "handbrakeMode",
                        "ffmpegMode",
                        "processFile",
                        "infoLog"
                      ]
                    }
                  },
                  "required": [
                    "details",
                    "conditionalsString",
                    "conditionalNotes",
                    "action"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "boolean"
            }
          }
        }
      }
    },
    "/api/v2/create-sample": {
      "post": {
        "description": "For creating a 30 second sample of a file",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "filePath": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "filePath"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "output": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "output": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/cruddb": {
      "post": {
        "description": "\nFor interacting with the database\n\ninsert:    requires collection, docID, obj (with keys/values to insert)\ngetById:   requires collection, docID\ngetByIndex:requires collection, docID\ngetAll:    requires collection\nupdate:    requires collection, docID, obj (with keys/values to update)\nremoveOne: requires collection, docID\nremoveAll: requires collection\n  ",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "collection",
                    "mode"
                  ],
                  "properties": {
                    "collection": {
                      "type": "string",
                      "enum": [
                        "SettingsGlobalJSONDB",
                        "LibrarySettingsJSONDB",
                        "NodeJSONDB",
                        "StatisticsJSONDB",
                        "VariablesJSONDB",
                        "UsersJSONDB",
                        "ApiKeysJSONDB",
                        "FlowsJSONDB",
                        "StagedJSONDB",
                        "FileJSONDB",
                        "F2FOutputJSONDB",
                        "WorkerVerdictHistoryJSONDB",
                        "JobsJSONDB"
                      ]
                    },
                    "mode": {
                      "type": "string",
                      "enum": [
                        "getById",
                        "getByIndex",
                        "getAll",
                        "insert",
                        "update",
                        "incdec",
                        "removeOne",
                        "removeByDB",
                        "removeAll"
                      ]
                    },
                    "docID": {
                      "type": "string",
                      "examples": [
                        "C:/mediaFile.mkv"
                      ]
                    },
                    "obj": {
                      "type": "object",
                      "examples": [
                        {
                          "createdAt": 1644381503446
                        }
                      ]
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "oneOf": [
                {
                  "type": "object",
                  "additionalProperties": true
                },
                {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": true
                  }
                }
              ]
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/debug-vars/{type}": {
      "get": {
        "description": "For getting various debug info",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/debug": {
      "get": {
        "description": "For getting a page with various debug info",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/delete-backup": {
      "post": {
        "description": "For deleting a backup of the Tdarr database",
        "tags": [
          "backups"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "name"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": [
                "string",
                "boolean"
              ]
            }
          }
        }
      }
    },
    "/api/v2/delete-cache-file": {
      "post": {
        "description": "For deleting a cache file",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "file": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "file"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/delete-file": {
      "post": {
        "description": "For deleting a file on disk of a file in Tdarr DB",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "file": {
                      "type": "object",
                      "properties": {
                        "_id": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "_id"
                      ]
                    }
                  },
                  "required": [
                    "file"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "message": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/delete-plugin": {
      "post": {
        "description": "For deleting a plugin",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "pluginSource": {
                      "type": "string"
                    },
                    "pluginID": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "pluginSource",
                    "pluginID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/delete-unhealthy-files": {
      "post": {
        "description": "For deleting files which have failed to transcode (table3) or unhealthy files (table6)",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "table": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "table"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/disconnect-node": {
      "post": {
        "description": "For forcefully disconnecting a node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/download-plugins": {
      "get": {
        "description": "For nodes to download the latest plugins zip",
        "tags": [
          "nodes",
          "plugins"
        ],
        "produces": [
          "application/zip"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/file/download": {
      "post": {
        "description": "For downloading a file",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string"
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "501": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/file/upload": {
      "post": {
        "description": "For uploading a file",
        "tags": [
          "nodes"
        ],
        "consumes": [
          "multipart/form-data"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "501": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/find-duplicates": {
      "post": {
        "description": "For starting the find duplicates process",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "threshold": {
                      "type": "number"
                    },
                    "count": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "threshold",
                    "count"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/get-backup-status": {
      "post": {
        "description": "For getting the status of a Tdarr backup in progress",
        "tags": [
          "backups"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "status": {
                    "type": "string"
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/get-backups": {
      "post": {
        "description": "For getting a list of backups of the Tdarr database",
        "tags": [
          "backups"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "size": {
                    "type": "string"
                  },
                  "statSync": {
                    "type": "object",
                    "additionalProperties": true
                  },
                  "date": {
                    "type": "number"
                  }
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/get-db-statuses": {
      "post": {
        "description": "For getting the statuses of the Tdarr database",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/get-filescanner-status": {
      "post": {
        "description": "For getting the status of a file scanner in progress",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/get-new-task": {
      "post": {
        "description": "For a node to request a new task",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID",
                    "workerID",
                    "workerType"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    },
                    "workerID": {
                      "type": "string"
                    },
                    "workerType": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "object",
                    "additionalProperties": true
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/get-node-log": {
      "post": {
        "description": "For getting the log of a node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/get-nodes": {
      "get": {
        "description": "For getting connected nodes information",
        "tags": [
          "nodes"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/get-res-stats": {
      "post": {
        "description": "For getting server resource information",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "process": {
                  "type": "object",
                  "properties": {
                    "uptime": {
                      "type": "integer"
                    },
                    "heapUsedMB": {
                      "type": "string"
                    },
                    "heapTotalMB": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "uptime",
                    "heapUsedMB",
                    "heapTotalMB"
                  ]
                },
                "os": {
                  "type": "object",
                  "properties": {
                    "cpuPerc": {
                      "type": "string"
                    },
                    "memUsedGB": {
                      "type": "string"
                    },
                    "memTotalGB": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "cpuPerc",
                    "memUsedGB",
                    "memTotalGB"
                  ]
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/get-server-log": {
      "get": {
        "description": "For getting the server log",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/get-subdirectories": {
      "post": {
        "description": "For getting subdirectories of a folder",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "folderPath": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "folderPath"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "valid": {
                  "type": "boolean"
                },
                "folders": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "fullPath": {
                        "type": "string"
                      },
                      "folder": {
                        "type": "string"
                      }
                    }
                  }
                },
                "warning": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/get-time-now": {
      "post": {
        "description": "For getting the current time on the server",
        "tags": [],
        "responses": {
          "200": {
            "description": "Time now",
            "schema": {
              "type": "integer",
              "description": "Time now"
            }
          }
        }
      }
    },
    "/api/v2/is-server-alive": {
      "post": {
        "description": "Old endpoint for checking if the server is alive (user 'status' instead)",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "isAlive": {
                  "type": "boolean"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/item-proc-end": {
      "post": {
        "description": "For when a node completes processing an item",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID",
                    "obj"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    },
                    "obj": {
                      "type": "object"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/kill-file-scanner": {
      "post": {
        "description": "For killing a file scanner in progress",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/kill-worker": {
      "post": {
        "description": "For killing a worker on a node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "nodeID": {
                      "type": "string",
                      "description": "The ID of the node where the worker is running."
                    },
                    "workerID": {
                      "type": "string",
                      "description": "The ID of the worker to kill."
                    }
                  },
                  "required": [
                    "nodeID",
                    "workerID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/list-footprintId-reports": {
      "post": {
        "description": "For listing all job reports for a specific footprintId",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "footprintId"
                  ],
                  "properties": {
                    "footprintId": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "/api/v2/log-job-report": {
      "post": {
        "description": "For updating a job report",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "date",
                    "job",
                    "text"
                  ],
                  "properties": {
                    "date": {
                      "type": "number"
                    },
                    "job": {
                      "type": "object"
                    },
                    "text": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/performance-stats": {
      "post": {
        "description": "For various performance stat info",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "performanceStats": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/poll-worker-limits": {
      "post": {
        "description": "For a node to get its worker limits and check if there's anything in the queue",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "workerLimits": {
                  "type": "object",
                  "properties": {
                    "healthcheckcpu": {
                      "type": "number"
                    },
                    "healthcheckgpu": {
                      "type": "number"
                    },
                    "transcodecpu": {
                      "type": "number"
                    },
                    "transcodegpu": {
                      "type": "number"
                    }
                  }
                },
                "queueLengths": {
                  "type": "object",
                  "properties": {
                    "healthcheckcpu": {
                      "type": "number"
                    },
                    "healthcheckgpu": {
                      "type": "number"
                    },
                    "transcodecpu": {
                      "type": "number"
                    },
                    "transcodegpu": {
                      "type": "number"
                    }
                  }
                },
                "processPriority": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/public/auth/login": {
      "post": {
        "description": "For logging in a user",
        "tags": [
          "users"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "username": {
                  "type": "string"
                },
                "password": {
                  "type": "string"
                }
              },
              "required": [
                "username",
                "password"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "token": {
                  "type": "string"
                }
              }
            }
          },
          "401": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/public/auth/register": {
      "post": {
        "description": "For registering a new user",
        "tags": [
          "users"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "username": {
                  "type": "string"
                },
                "password": {
                  "type": "string"
                }
              },
              "required": [
                "username",
                "password"
              ]
            }
          }
        ],
        "responses": {
          "201": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "token": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "500": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/read-job-file": {
      "post": {
        "description": "For reading a job report",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "footprintId",
                    "jobId",
                    "jobFileId"
                  ],
                  "properties": {
                    "footprintId": {
                      "type": "string"
                    },
                    "jobId": {
                      "type": "string"
                    },
                    "jobFileId": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "text": {
                  "type": "string"
                },
                "isJobRunning": {
                  "type": "boolean",
                  "example": true
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "text": {
                  "type": "string"
                },
                "isJobRunning": {
                  "type": "boolean",
                  "example": false
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/read-plugin-text": {
      "post": {
        "description": "For the classic plugin editor to read a plugin file",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "pluginSource": {
                      "type": "string"
                    },
                    "pluginID": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "pluginSource",
                    "pluginID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/read-plugin": {
      "post": {
        "description": "For a node to read a plugin",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "plugin"
                  ],
                  "properties": {
                    "plugin": {
                      "type": "object",
                      "required": [
                        "source",
                        "id"
                      ],
                      "properties": {
                        "source": {
                          "type": "string"
                        },
                        "id": {
                          "type": "string"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "pluginRaw": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/remove-audio-codec-exclude": {
      "post": {
        "description": "For removing an audio codec to be excluded/included in basic audio transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/remove-library-files": {
      "post": {
        "description": "For removing all files from a Tdarr library DB, files on disk aren't removed",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "DB": {
                      "type": "string",
                      "description": "The ID of the library to remove files from."
                    }
                  },
                  "required": [
                    "DB"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/remove-plugin-include": {
      "post": {
        "description": "For removing a plugin from a classic plugin stack",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/remove-video-codec-exclude": {
      "post": {
        "description": "For removing an video codec to be excluded/included in basic video transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/rescan-file": {
      "post": {
        "description": "For rescanning a file",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "DB": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "_id",
                    "DB"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/reset-backup-status": {
      "post": {
        "description": "For resetting the backup status",
        "tags": [
          "backups"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/restart-node": {
      "post": {
        "description": "For restarting a specific node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "nodeID": {
                      "type": "string",
                      "description": "The ID of the node to restart."
                    }
                  },
                  "required": [
                    "nodeID"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/restart-server": {
      "post": {
        "description": "For restarting Tdarr Server",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/restart-ui": {
      "get": {
        "description": "For restarting the UI",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/run-help-command": {
      "post": {
        "description": "For running an ffmpeg or handbrake help command on the Help tab",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "mode": {
                      "type": "string"
                    },
                    "text": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "mode",
                    "text"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/save-plugin-text": {
      "post": {
        "description": "For the classic plugin editor to save plugin text",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "pluginSource": {
                      "type": "string"
                    },
                    "pluginID": {
                      "type": "string"
                    },
                    "text": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "pluginSource",
                    "pluginID",
                    "text"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/scan-files": {
      "post": {
        "description": "\n  For running a scanFresh, scanFindNew or scanFolderWatcher on a library\n  scanFresh & scanFindNew require a single string directory path\n  scanFolderWatcher requires an array of file paths to scanned\n  ",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "scanConfig": {
                      "type": "object",
                      "properties": {
                        "dbID": {
                          "type": "string"
                        },
                        "mode": {
                          "type": "string",
                          "enum": [
                            "scanFresh",
                            "scanFindNew",
                            "scanFolderWatcher"
                          ]
                        },
                        "arrayOrPath": {
                          "oneOf": [
                            {
                              "type": "string"
                            },
                            {
                              "type": "array",
                              "items": {
                                "type": "string"
                              }
                            }
                          ]
                        }
                      },
                      "required": [
                        "dbID",
                        "mode",
                        "arrayOrPath"
                      ]
                    }
                  },
                  "required": [
                    "scanConfig"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/scan-individual-file": {
      "post": {
        "description": "For scanning an individual file with various tools",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "scanTypes": {
                      "type": "object",
                      "properties": {
                        "exifToolScan": {
                          "type": "boolean"
                        },
                        "mediaInfoScan": {
                          "type": "boolean"
                        },
                        "closedCaptionScan": {
                          "type": "boolean"
                        }
                      },
                      "required": [
                        "exifToolScan",
                        "mediaInfoScan",
                        "closedCaptionScan"
                      ]
                    },
                    "file": {
                      "type": "object",
                      "properties": {
                        "file": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "file"
                      ]
                    }
                  },
                  "required": [
                    "scanTypes",
                    "file"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {
                "_id": {
                  "type": "string"
                },
                "file": {
                  "type": "string"
                },
                "DB": {
                  "type": "string"
                },
                "footprintId": {
                  "type": "string"
                },
                "container": {
                  "type": "string"
                },
                "scannerReads": {
                  "type": "object",
                  "properties": {
                    "ffProbeRead": {
                      "type": "string"
                    },
                    "exiftoolRead": {
                      "type": "string"
                    },
                    "mediaInfoRead": {
                      "type": "string"
                    },
                    "closedCaptionRead": {
                      "type": "string"
                    }
                  }
                },
                "ffprobeData": {
                  "type": "object",
                  "additionalProperties": true
                },
                "meta": {
                  "type": "object",
                  "additionalProperties": true
                },
                "mediaInfo": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/search-db": {
      "post": {
        "description": "Old endpoint for searching the file database (use 'client' endpoint instead)",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "string": {
                      "type": "string"
                    },
                    "greaterThanGB": {
                      "type": "number"
                    },
                    "lessThanGB": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "string",
                    "greaterThanGB",
                    "lessThanGB"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": true,
                "properties": {

                }
              }
            }
          }
        }
      }
    },
    "/api/v2/search-flow-plugins": {
      "post": {
        "description": "For searching flow plugins",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "string": {
                      "type": "string"
                    },
                    "pluginType": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "string",
                    "pluginType"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": true,
                      "properties": {

                      }
                    }
                  },
                  {
                    "type": "string"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/search-flow-templates": {
      "post": {
        "description": "For searching flow templates",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "string": {
                      "type": "string"
                    },
                    "pluginType": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "string",
                    "pluginType"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": true,
                      "properties": {

                      }
                    }
                  },
                  {
                    "type": "string"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/search-job-reports": {
      "post": {
        "description": "For searching job reports",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "searchTerms"
                  ],
                  "properties": {
                    "searchTerms": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "jobReports": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "filename": {
                        "type": "string"
                      },
                      "lastModifiedMs": {
                        "type": "number"
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/search-plugins": {
      "post": {
        "description": "For searching classic plugins",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "string": {
                      "type": "string"
                    },
                    "pluginType": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "string",
                    "pluginType"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": true,
                      "properties": {
                        "Name": {
                          "type": "string"
                        },
                        "Type": {
                          "type": "string"
                        },
                        "Operation": {
                          "type": "string"
                        },
                        "Description": {
                          "type": "string"
                        },
                        "Version": {
                          "type": "string"
                        },
                        "Link": {
                          "type": "string"
                        },
                        "source": {
                          "type": "string"
                        }
                      }
                    }
                  },
                  {
                    "type": "string"
                  }
                ]
              }
            }
          }
        }
      }
    },
    "/api/v2/set-all-status": {
      "post": {
        "description": "For requeueing files for transcode or health check for a specific library",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "mode": {
                      "type": "string"
                    },
                    "table": {
                      "type": "string"
                    },
                    "processStatus": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "mode",
                    "table",
                    "processStatus"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-pies": {
      "post": {
        "description": "For getting all or library pie stats",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "libraryId": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "pieStats": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-res-hist": {
      "post": {
        "description": "For getting server resource history",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "timeframe": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "rows": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "c": {
                        "type": "number"
                      },
                      "hU": {
                        "type": "number"
                      },
                      "hT": {
                        "type": "number"
                      },
                      "cP": {
                        "type": "number"
                      },
                      "mU": {
                        "type": "number"
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-running-worker-hist": {
      "post": {
        "description": "For getting running worker history",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "timeframe": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "rows": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "timestamp": {
                        "type": "number"
                      },
                      "c": {
                        "type": "number"
                      },
                      "tcpu": {
                        "type": "number"
                      },
                      "tgpu": {
                        "type": "number"
                      },
                      "hcpu": {
                        "type": "number"
                      },
                      "hgpu": {
                        "type": "number"
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-space-saved": {
      "post": {
        "description": "For getting space saved history",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "libraryId": {
                      "type": "string"
                    },
                    "timeframe": {
                      "type": "string"
                    },
                    "nodeId": {
                      "type": "string"
                    },
                    "workerType": {
                      "type": "string"
                    },
                    "pluginId": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "buckets": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "space_saved": {
                        "type": "number"
                      },
                      "bucket": {
                        "type": "string"
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-streams": {
      "post": {
        "description": "For getting stream stats info",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "libraryId": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "streamInfo": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/get-worker-verdict-hist": {
      "post": {
        "description": "For getting worker verdict history",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "timeframe": {
                      "type": "string"
                    },
                    "libraryId": {
                      "type": "string"
                    },
                    "nodeId": {
                      "type": "string"
                    },
                    "workerType": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "buckets": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "bucket": {
                        "type": "string"
                      },
                      "tSuc": {
                        "type": "number"
                      },
                      "tErr": {
                        "type": "number"
                      },
                      "tNq": {
                        "type": "number"
                      },
                      "hSuc": {
                        "type": "number"
                      },
                      "hErr": {
                        "type": "number"
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "403": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/stats/space-saved-add": {
      "post": {
        "description": "For adding space saved record",
        "tags": [
          "stats"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "libraryId": {
                      "type": "string"
                    },
                    "spaceSaved": {
                      "type": "number"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/status": {
      "get": {
        "description": "For checking server status",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "status": {
                  "type": "string"
                },
                "isProduction": {
                  "type": "boolean"
                },
                "os": {
                  "type": "string"
                },
                "version": {
                  "type": "string"
                },
                "uptime": {
                  "type": "integer"
                }
              }
            }
          }
        }
      }
    },
    "/api/v2/stop-dedupe": {
      "get": {
        "description": "For stopping the dedupe process",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/sync-plugins": {
      "post": {
        "description": "For syncing plugins from server to all nodes",
        "tags": [
          "nodes",
          "plugins"
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/toggle-folder-watch": {
      "post": {
        "description": "For enabling/disabling folder watching on a library",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "auto": {
                      "type": "boolean",
                      "description": "Whether request has been triggered automatically (true) or by user (false)."
                    },
                    "folder": {
                      "type": "string",
                      "description": "The path to the folder to watch."
                    },
                    "dbID": {
                      "type": "string",
                      "description": "The library ID."
                    },
                    "status": {
                      "type": "boolean",
                      "description": "If the folder watcher should be enabled or disabled."
                    }
                  },
                  "required": [
                    "auto",
                    "folder",
                    "dbID",
                    "status"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/toggle-schedule": {
      "post": {
        "description": "For updating the schedule of a library",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "start": {
                      "type": "integer"
                    },
                    "end": {
                      "type": "integer"
                    },
                    "type": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "dbID",
                    "start",
                    "end",
                    "type"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/transcode-user-verdict": {
      "post": {
        "description": "For taking action on a staged item",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "obj",
                    "verdict"
                  ],
                  "properties": {
                    "obj": {
                      "type": "object"
                    },
                    "verdict": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-audio-codec-exclude": {
      "post": {
        "description": "For updating an audio codec to be excluded/included in basic audio transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    },
                    "status": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele",
                    "status"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-node-relay": {
      "post": {
        "description": "For nodes to update the server with their status",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "required": [
                "data"
              ],
              "properties": {
                "data": {
                  "type": "object",
                  "required": [
                    "nodeID",
                    "resStats",
                    "workers"
                  ],
                  "properties": {
                    "nodeID": {
                      "type": "string"
                    },
                    "resStats": {
                      "type": "object"
                    },
                    "workers": {
                      "type": "object"
                    }
                  }
                }
              }
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-node": {
      "post": {
        "description": "For the UI to update a connected node",
        "tags": [
          "nodes"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "nodeID": {
                      "type": "string",
                      "description": "The ID of the node to update."
                    },
                    "nodeUpdates": {
                      "type": "object",
                      "description": "The updates to apply to the node."
                    }
                  },
                  "required": [
                    "nodeID",
                    "nodeUpdates"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-plugin-include": {
      "post": {
        "description": "For enabling/disabling a plugin in a classic plugin stack",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    },
                    "status": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele",
                    "status"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-plugins": {
      "post": {
        "description": "For requesting the server to update community plugins",
        "tags": [
          "plugins"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "force": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "force"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-schedule-block": {
      "post": {
        "description": "For updating a block in a library schedule",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    },
                    "status": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele",
                    "status"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/update-video-codec-exclude": {
      "post": {
        "description": "For updating an video codec to be excluded/included in basic video transcoding settings",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "dbID": {
                      "type": "string"
                    },
                    "ele": {
                      "type": "string"
                    },
                    "status": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "dbID",
                    "ele",
                    "status"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/updater/check": {
      "post": {
        "description": "For checking if an update is available",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "resetUpdater": {
                  "type": "boolean"
                },
                "downloadUpdate": {
                  "type": "boolean"
                },
                "applyUpdate": {
                  "type": "boolean"
                }
              },
              "required": [
                "downloadUpdate",
                "applyUpdate",
                "resetUpdater"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "properties": {
                "newVersionAvailable": {
                  "type": "boolean"
                },
                "currentVersion": {
                  "type": "string"
                },
                "requiredVersion": {
                  "type": "string"
                },
                "message": {
                  "type": "string"
                }
              }
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/updater/package-index": {
      "post": {
        "description": "For getting the package index",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/updater/relaunch": {
      "post": {
        "description": "For relaunching Tdarr Server when an update is ready",
        "tags": [],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          },
          "400": {
            "description": "Default Response",
            "schema": {
              "type": "string"
            }
          }
        }
      }
    },
    "/api/v2/use-token": {
      "post": {
        "description": "For using a token",
        "tags": [],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "token": {
                      "type": "string"
                    },
                    "redirect": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "token",
                    "redirect"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "object",
              "additionalProperties": true,
              "properties": {

              }
            }
          }
        }
      }
    },
    "/api/v2/verify-folder-exists": {
      "post": {
        "description": "For verifying if a folder exists",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "folderPath": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "folderPath"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "boolean"
            }
          }
        }
      }
    },
    "/api/v2/verify-plugin": {
      "post": {
        "description": "For verifying if a classic plugin exists",
        "tags": [
          "libraries"
        ],
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "properties": {
                    "pluginID": {
                      "type": "string"
                    },
                    "community": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "pluginID",
                    "community"
                  ]
                }
              },
              "required": [
                "data"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Default Response",
            "schema": {
              "type": "boolean"
            }
          }
        }
      }
    }
  },
  "tags": [
    {
      "name": "libraries"
    },
    {
      "name": "plugins"
    },
    {
      "name": "nodes"
    },
    {
      "name": "backups"
    },
    {
      "name": "stats"
    },
    {
      "name": "users"
    }
  ],
  "externalDocs": {

  }
}
