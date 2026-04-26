import type { Core } from '@strapi/strapi';

export default {
  register(/* { strapi }: { strapi: Core.Strapi } */) {},

  async bootstrap({ strapi }: { strapi: Core.Strapi }) {
    const hotelCount = await strapi.db.query('api::hotel.hotel').count();

    if (hotelCount === 0) {
      // Seed: RoomTypes
      const rt1 = await strapi.db.query('api::room-type.room-type').create({
        data: { roomTypeCode: 'DLX', roomTypeName: '豪华大床房', bedCount: 1, maxCheckInCount: 2, sort: 1 },
      });
      const rt2 = await strapi.db.query('api::room-type.room-type').create({
        data: { roomTypeCode: 'TWN', roomTypeName: '标准双床房', bedCount: 2, maxCheckInCount: 3, sort: 2 },
      });
      const rt3 = await strapi.db.query('api::room-type.room-type').create({
        data: { roomTypeCode: 'SUT', roomTypeName: '套房', bedCount: 1, maxCheckInCount: 4, sort: 3 },
      });

      // Seed: Hotel 1001
      const hotel1 = await strapi.db.query('api::hotel.hotel').create({
        data: {
          chainId: 1001,
          chainName: '亚朵·测试酒店北京',
          status: 3,
          step: 3,
          cityId: 110000,
          areaId: 110100,
          address: '北京市朝阳区测试路1号',
          telephone: '010-12345678',
        },
      });
      for (let i = 1; i <= 5; i++) {
        await strapi.db.query('api::room.room').create({
          data: {
            roomNo: `10${i}`,
            floor: 1,
            hotel: hotel1.id,
            roomType: i <= 3 ? rt1.id : rt2.id,
          },
        });
      }

      // Seed: Hotel 1002
      const hotel2 = await strapi.db.query('api::hotel.hotel').create({
        data: {
          chainId: 1002,
          chainName: '亚朵·测试酒店上海',
          status: 3,
          step: 3,
          cityId: 310000,
          areaId: 310100,
          address: '上海市浦东新区测试路2号',
          telephone: '021-87654321',
        },
      });
      for (let i = 1; i <= 5; i++) {
        await strapi.db.query('api::room.room').create({
          data: {
            roomNo: `20${i}`,
            floor: 2,
            hotel: hotel2.id,
            roomType: i <= 2 ? rt3.id : rt2.id,
          },
        });
      }

      strapi.log.info('Seed data inserted: 2 hotels, 10 rooms, 3 room types');
    }
  },
};
