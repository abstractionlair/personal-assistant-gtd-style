/**
 * Module: errors
 * Purpose: Define error hierarchy for graph memory operations and MCP responses.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import type { GraphMemoryErrorCode, GraphMemoryErrorPayload } from './types.js';

/**
 * Base error that captures MCP payload formatting.
 */
export class GraphMemoryError extends Error {
  /**
   * Machine-readable code for downstream handling.
   */
  public readonly code: GraphMemoryErrorCode;

  /**
   * Optional details block surfaced to clients.
   */
  public readonly details?: Record<string, unknown>;

  constructor(code: GraphMemoryErrorCode, message: string, details?: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.details = details;
  }

  /**
   * Convert to MCP-friendly payload with structuredContent.
   */
  toPayload(): GraphMemoryErrorPayload {
    return {
      code: this.code,
      message: this.message,
      ...(this.details ? { details: this.details } : {})
    };
  }
}

export class OntologyNotFoundError extends GraphMemoryError {
  constructor() {
    super('ONTOLOGY_NOT_FOUND', 'Ontology has not been created yet');
  }
}

export class OntologyAlreadyExistsError extends GraphMemoryError {
  constructor() {
    super('ONTOLOGY_ALREADY_EXISTS', 'Ontology already exists and cannot be recreated');
  }
}

export class TypeAlreadyExistsError extends GraphMemoryError {
  constructor(typeName: string) {
    super('TYPE_ALREADY_EXISTS', `Type already exists in ontology: ${typeName}`, { typeName });
  }
}

export class InvalidNodeTypeError extends GraphMemoryError {
  constructor(typeName: string) {
    super('INVALID_NODE_TYPE', `Node type is not defined in ontology: ${typeName}`, { typeName });
  }
}

export class InvalidConnectionTypeError extends GraphMemoryError {
  constructor(typeName: string) {
    super('INVALID_CONNECTION_TYPE', `Connection type is not defined in ontology: ${typeName}`, { typeName });
  }
}

export class InvalidTopologyError extends GraphMemoryError {
  constructor(
    connectionType: string,
    fromType: string,
    toType: string,
    options?: { allowedFrom?: string[]; allowedTo?: string[] }
  ) {
    const allowedFrom = options?.allowedFrom ?? [];
    const allowedTo = options?.allowedTo ?? [];
    const allowedFragments: string[] = [];
    if (allowedFrom.length > 0) {
      allowedFragments.push(`Valid sources: [${allowedFrom.join(', ')}]`);
    }
    if (allowedTo.length > 0) {
      allowedFragments.push(`Valid targets: [${allowedTo.join(', ')}]`);
    }
    const suffix = allowedFragments.length > 0 ? `. ${allowedFragments.join(' ')}` : '';
    super(
      'INVALID_TOPOLOGY',
      `Connection type ${connectionType} cannot connect ${fromType} → ${toType}${suffix}`,
      {
        connectionType,
        fromType,
        toType,
        ...(allowedFrom.length > 0 ? { allowedFrom } : {}),
        ...(allowedTo.length > 0 ? { allowedTo } : {})
      }
    );
  }
}

export class RequiredPropertyMissingError extends GraphMemoryError {
  constructor(connectionType: string, requiredProperties: string[], missing?: string[]) {
    const missingList = missing ?? [];
    const missingSuffix = missingList.length > 0 ? `. Missing: ${missingList.join(', ')}` : '';
    super(
      'REQUIRED_PROPERTY_MISSING',
      `Connection type ${connectionType} requires properties: ${requiredProperties.join(', ')}${missingSuffix}`,
      {
        connectionType,
        requiredProperties,
        ...(missingList.length > 0 ? { missing: missingList } : {})
      }
    );
  }
}

export class NodeNotFoundError extends GraphMemoryError {
  constructor(nodeId: string) {
    super('NODE_NOT_FOUND', `Node not found: ${nodeId}`, { nodeId });
  }
}

export class ConnectionNotFoundError extends GraphMemoryError {
  constructor(connectionId: string) {
    super('CONNECTION_NOT_FOUND', `Connection not found: ${connectionId}`, { connectionId });
  }
}

export class FileCreationFailedError extends GraphMemoryError {
  constructor(path: string, cause?: unknown) {
    super('FILE_CREATION_FAILED', `Failed to create file: ${path}`, { path, cause });
  }
}

export class ContentReadFailedError extends GraphMemoryError {
  constructor(path: string, cause?: unknown) {
    super('CONTENT_READ_FAILED', `Failed to read content from: ${path}`, { path, cause });
  }
}

export class InvalidEncodingError extends GraphMemoryError {
  constructor() {
    super('INVALID_ENCODING', 'Encoding must be provided when content is supplied');
  }
}

export class InvalidArgumentError extends GraphMemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super('INVALID_ARGUMENT', message, details);
  }
}

/**
 * Raised for stubbed methods awaiting implementation.
 */
export class NotImplementedError extends Error {
  constructor(message: string) {
    super(message);
  }
}
