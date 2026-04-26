import { describe, it, expect } from 'vitest';

import hotelSchema from '../src/api/hotel/content-types/hotel/schema.json';
import roomSchema from '../src/api/room/content-types/room/schema.json';
import roomTypeSchema from '../src/api/room-type/content-types/room-type/schema.json';

describe('Hotel schema', () => {
  it('has required chainId field as unique integer', () => {
    const { chainId } = hotelSchema.attributes;
    expect(chainId.type).toBe('integer');
    expect(chainId.unique).toBe(true);
    expect(chainId.required).toBe(true);
  });

  it('has chainName as required string', () => {
    const { chainName } = hotelSchema.attributes;
    expect(chainName.type).toBe('string');
    expect(chainName.required).toBe(true);
  });

  it('has rooms oneToMany relation', () => {
    const { rooms } = hotelSchema.attributes;
    expect(rooms.type).toBe('relation');
    expect(rooms.relation).toBe('oneToMany');
    expect(rooms.target).toBe('api::room.room');
  });

  it('has status field with default 1', () => {
    expect(hotelSchema.attributes.status.type).toBe('integer');
    expect(hotelSchema.attributes.status.default).toBe(1);
  });

  it('has step field with default 0', () => {
    expect(hotelSchema.attributes.step.type).toBe('integer');
    expect(hotelSchema.attributes.step.default).toBe(0);
  });

  it('has openDate as datetime', () => {
    expect(hotelSchema.attributes.openDate.type).toBe('datetime');
  });

  it('has address, telephone, cityId, areaId, dbName, instance fields', () => {
    expect(hotelSchema.attributes.address.type).toBe('string');
    expect(hotelSchema.attributes.telephone.type).toBe('string');
    expect(hotelSchema.attributes.cityId.type).toBe('integer');
    expect(hotelSchema.attributes.areaId.type).toBe('integer');
    expect(hotelSchema.attributes.dbName.type).toBe('string');
    expect(hotelSchema.attributes.instance.type).toBe('string');
  });
});

describe('Room schema', () => {
  it('has required roomNo field', () => {
    expect(roomSchema.attributes.roomNo.type).toBe('string');
    expect(roomSchema.attributes.roomNo.required).toBe(true);
  });

  it('has floor as integer', () => {
    expect(roomSchema.attributes.floor.type).toBe('integer');
  });

  it('has manyToOne relation to hotel', () => {
    const { hotel } = roomSchema.attributes;
    expect(hotel.relation).toBe('manyToOne');
    expect(hotel.target).toBe('api::hotel.hotel');
  });

  it('has manyToOne relation to roomType', () => {
    const { roomType } = roomSchema.attributes;
    expect(roomType.relation).toBe('manyToOne');
    expect(roomType.target).toBe('api::room-type.room-type');
  });
});

describe('RoomType schema', () => {
  it('has unique required roomTypeCode', () => {
    const { roomTypeCode } = roomTypeSchema.attributes;
    expect(roomTypeCode.type).toBe('string');
    expect(roomTypeCode.unique).toBe(true);
    expect(roomTypeCode.required).toBe(true);
  });

  it('has roomTypeName as required string', () => {
    const { roomTypeName } = roomTypeSchema.attributes;
    expect(roomTypeName.type).toBe('string');
    expect(roomTypeName.required).toBe(true);
  });

  it('has bedCount default 1', () => {
    expect(roomTypeSchema.attributes.bedCount.default).toBe(1);
  });

  it('has maxCheckInCount default 2', () => {
    expect(roomTypeSchema.attributes.maxCheckInCount.default).toBe(2);
  });

  it('has sort default 0', () => {
    expect(roomTypeSchema.attributes.sort.default).toBe(0);
  });

  it('has rooms oneToMany relation', () => {
    const { rooms } = roomTypeSchema.attributes;
    expect(rooms.type).toBe('relation');
    expect(rooms.relation).toBe('oneToMany');
    expect(rooms.target).toBe('api::room.room');
  });
});
